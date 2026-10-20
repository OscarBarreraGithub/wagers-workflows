#!/usr/bin/env python3
"""Build a new release at its final prefix; no scheduler/remote operations."""
import sys

# Shared software must stay byte-for-byte unchanged, including import caches.
sys.dont_write_bytecode = True

import argparse
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
import wagers


def absolute(value):
    p = Path(value).expanduser()
    def check_text(path):
        if not str(path).isascii() or any(ord(c) < 32 or ord(c) == 127 for c in str(path)):
            raise ValueError("Deployment paths must use printable ASCII (spaces allowed); choose a path without Unicode/control characters")
    check_text(p)
    if not p.is_absolute() or "REQUIRED" in str(p):
        raise ValueError("Fill every required absolute deployment path")
    if p.is_symlink():
        raise ValueError("Deployment path must not be a symlink")
    resolved = p.resolve()
    check_text(resolved)
    return resolved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    prefix = absolute(cfg["release_prefix"])
    modules = absolute(cfg["module_root"])
    name = cfg["module_name"]
    if not re.fullmatch(r"[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+", name):
        raise ValueError("module_name must be name/version")
    if cfg.get("python_module") != "python":
        raise ValueError("This bootstrap requires the site's reviewed `module load python` setup")
    modulefile = modules / (name + ".lua")
    if prefix.exists() or modulefile.exists():
        raise ValueError("New release prefix/module required; existing releases are never overwritten")
    if prefix in REPO.parents or prefix == REPO or REPO in prefix.parents:
        raise ValueError("Install outside the onboarding repository")
    mamba = shutil.which("mamba")
    if not mamba:
        raise ValueError("mamba not found: use FASRC's module load python environment")
    prefix.mkdir(parents=True)
    evidence = prefix / "provenance"
    evidence.mkdir()
    state = {"status": "building", "config": cfg, "package_version": wagers.VERSION}
    statefile = evidence / "build.json"
    wagers.write_json(statefile, state)
    try:
        wagers.fetch_source(prefix / "upstream")
        env = prefix / "env"
        recipe = REPO / "environment.yml"
        shutil.copyfile(recipe, evidence / "environment.candidate.yml")
        command = [mamba, "env", "create", "--prefix", str(env), "--file", str(recipe), "--yes"]
        state["create_command"] = command
        wagers.write_json(statefile, state)
        with (evidence / "environment-build.log").open("w") as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        for command, filename in [
            ([mamba, "list", "--prefix", str(env), "--explicit"], "environment.explicit.txt"),
            ([mamba, "env", "export", "--prefix", str(env)], "environment.resolved.yml"),
        ]:
            with (evidence / filename).open("w") as out:
                subprocess.run(command, stdout=out, check=True)
        app = prefix / "app"
        app.mkdir()
        shutil.copyfile(REPO / "wagers.py", app / "wagers.py")
        shutil.copytree(REPO / "scripts", app / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        bindir = prefix / "bin"
        bindir.mkdir()
        launcher = bindir / "wagers-myotally"
        launcher.write_text(
            "#!/usr/bin/env bash\nset -euo pipefail\nunset PYTHONPATH\n"
            "export PYTHONNOUSERSITE=1\n"
            f"export WAGERS_MYOTALLY_SOURCE={shlex.quote(str(prefix / 'upstream' / 'source'))}\n"
            f"exec {shlex.quote(mamba)} run --prefix {shlex.quote(str(env))} "
            f"python -B -I {shlex.quote(str(app / 'wagers.py'))} \"$@\"\n"
        )
        launcher.chmod(0o755)
        subprocess.run([str(launcher), "doctor"], check=True)
        # Write Lmod only after a successful environment/import check. This is
        # still not an image-run acceptance or a lab-access check.
        modulefile.parent.mkdir(parents=True, exist_ok=True)
        module_text = (
            'help([[Wagers Myotally: CPU runtime; biological validation pending.]])\n'
            'whatis("Pinned Myotally 1.0.2 safe CLI, environment 001")\n'
            'depends_on("python")\n'
            f'prepend_path("PATH", {json.dumps(str(bindir))})\n'
            f'setenv("WAGERS_MYOTALLY_PREFIX", {json.dumps(str(prefix))})\n'
        )
        with modulefile.open("x") as output:
            output.write(module_text)
        state.update(status="built-image-validation-pending", modulefile=str(modulefile),
                     wrapper_sha256=wagers.sha256(app / "wagers.py"))
        print(json.dumps({"launcher": str(launcher), "modulefile": str(modulefile),
                          "next": f"{launcher} doctor; then scripts/validate_one.py"}, indent=2))
    except Exception as exc:
        state.update(status="failed", error=str(exc))
        raise
    finally:
        wagers.write_json(statefile, state)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"BOOTSTRAP FAILED: {exc}", file=sys.stderr)
        sys.exit(2)
