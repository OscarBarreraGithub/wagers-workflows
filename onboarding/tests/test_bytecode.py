"""Bytecode/process contracts only; argv stubs never stand in for upstream runs."""
import sys
sys.dont_write_bytecode = True

import ast
import contextlib
import io
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
sys.path.insert(0, str(PACKAGE / "scripts"))
import wagers
import bootstrap


class BytecodeContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="myotally bytecode ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def test_isolation_ignores_environment_but_explicit_B_prevents_cache(self):
        # Real interpreters/imports into writable scratch space demonstrate the
        # failure mode; no upstream or installed environment is altered.
        for flags, expected in [(["-I"], False), (["-B", "-I"], True)]:
            source = self.root / str(expected)
            source.mkdir()
            (source / "probe.py").write_text("VALUE = 1\n")
            code = ("import sys; sys.path.insert(0, sys.argv[1]); "
                    "import probe; print(sys.dont_write_bytecode)")
            result = subprocess.run([sys.executable, *flags, "-c", code, str(source)],
                                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                                    capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout.strip(), str(expected))
            self.assertEqual(bool(list(source.rglob("*.pyc"))), not expected)

    def test_helper_startup_and_explicit_B_imports_leave_source_cache_free(self):
        app = self.root / "app"
        (app / "scripts").mkdir(parents=True)
        shutil.copyfile(PACKAGE / "wagers.py", app / "wagers.py")
        helpers = ["bootstrap", "validate_one", "tutorial_suite", "make_control", "make_tutorial"]
        for name in helpers:
            shutil.copyfile(PACKAGE / "scripts" / (name + ".py"), app / "scripts" / (name + ".py"))
        # run_path models script execution (scripts themselves are not cached).
        # No -B here: each entry must suppress caches before its local imports.
        for path in [app / "wagers.py", *[app / "scripts" / (n + ".py") for n in helpers]]:
            code = "import runpy, sys; runpy.run_path(sys.argv[1], run_name='startup_probe'); assert sys.dont_write_bytecode"
            subprocess.run([sys.executable, "-I", "-c", code, str(path)], check=True)
            self.assertEqual(list(app.rglob("__pycache__")), [])
        # Ordinary import can cache the imported entry before its body executes;
        # explicit -B must protect direct imports as well as their dependencies.
        code = ("import importlib, sys; sys.path.insert(0, sys.argv[1]); "
                "[importlib.import_module(n) for n in sys.argv[2:]]")
        subprocess.run([sys.executable, "-B", "-I", "-c", code, str(app / "scripts"), *helpers], check=True)
        self.assertEqual(list(app.rglob("__pycache__")), [])
        self.assertEqual(list(app.rglob("*.pyc")), [])

    def test_all_isolated_child_arrays_and_dispatch_arguments(self):
        # Inspect every interpreter array, including nested runner/worker paths;
        # fail if an added child drops either explicit flag.
        expected_counts = {"wagers.py": 3, "scripts/validate_one.py": 1, "scripts/tutorial_suite.py": 1}
        for name, count in expected_counts.items():
            tree = ast.parse((PACKAGE / name).read_text())
            arrays = [n for n in ast.walk(tree) if isinstance(n, ast.List) and n.elts
                      and ast.unparse(n.elts[0]) == "sys.executable"]
            self.assertEqual(len(arrays), count, name)
            for node in arrays:
                self.assertEqual([ast.literal_eval(n) for n in node.elts[1:3]], ["-B", "-I"], name)
        # Argv-only stubs: these do not execute a tutorial suite or upstream.
        evidence, source = self.root / "output with spaces", self.root / "source with spaces"
        args = wagers.parser().parse_args(["tutorial-suite", "--evidence-dir", str(evidence), "--source", str(source)])
        with patch.object(wagers.subprocess, "run") as run:
            args.func(args)
        run.assert_called_once_with([sys.executable, "-B", "-I", str(PACKAGE / "scripts/tutorial_suite.py"),
                                     "--evidence-dir", str(evidence), "--source", str(source)], check=True)
        args = wagers.parser().parse_args(["validate-one", "--evidence-dir", str(evidence),
                                          "--manifest", str(self.root / "manifest with spaces.csv"),
                                          "--min-area", "50", "--max-area", "750", "--quality", "low"])
        with patch.object(wagers.subprocess, "run") as run:
            args.func(args)
        run.assert_called_once_with([sys.executable, "-B", "-I", str(PACKAGE / "scripts/validate_one.py"),
                                     "--evidence-dir", str(evidence), "--min-area", "50.0", "--max-area", "750.0",
                                     "--quality", "low", "--manifest", str(args.manifest)], check=True)

    def test_generated_launcher_and_bootstrap_shell_flags(self):
        # Stub only installation operations, then inspect the actual generated
        # launcher. No environment install, source download or doctor is run.
        prefix = self.root / "release with spaces"
        config = self.root / "deploy.json"
        config.write_text(json.dumps({"release_prefix": str(prefix), "module_root": str(self.root / "modules"),
                                      "module_name": "myotally/test", "python_module": "python"}))
        mamba = str(self.root / "mamba with spaces")
        with patch.object(sys, "argv", ["bootstrap.py", "--config", str(config)]), \
             patch.object(bootstrap.shutil, "which", return_value=mamba), \
             patch.object(bootstrap.wagers, "fetch_source"), \
             patch.object(bootstrap.subprocess, "run"), contextlib.redirect_stdout(io.StringIO()):
            bootstrap.main()
        line = (prefix / "bin/wagers-myotally").read_text().splitlines()[-1]
        self.assertEqual(shlex.split(line), ["exec", mamba, "run", "--prefix", str(prefix / "env"),
                                            "python", "-B", "-I", str(prefix / "app/wagers.py"), "$@"])
        self.assertIn('exec python -B "', (PACKAGE / "scripts/bootstrap.sh").read_text())


if __name__ == "__main__":
    unittest.main()
