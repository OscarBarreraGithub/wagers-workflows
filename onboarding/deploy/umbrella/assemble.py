#!/usr/bin/env python3
"""Assemble wrappers for existing installed runtimes; never execute them."""
import argparse
import json
from pathlib import Path
import re
import shlex
import sys

sys.dont_write_bytecode = True
from launcher import absolute, digest, inspect, overlap, require

SCHEMA = {
    'schema_version', 'release_prefix', 'module_root', 'module_name', 'python_module',
    'host_prefix', 'host_python', 'myotally', 'imagej', 'cellprofiler', 'scanpy', 'adaptive_screen',
}
FIELDS = {'myotally': {'prefix'}, 'imagej': {'source'}, 'cellprofiler': {'source', 'sif', 'runtime'},
          'scanpy': {'source', 'runtime_prefix'}, 'adaptive_screen': {'source', 'runtime_prefix', 'receipt'}}


def assemble(config_path):
    config_path = absolute(str(config_path))
    raw = config_path.read_bytes()
    cfg = json.loads(raw)
    require(set(cfg) == SCHEMA and cfg['schema_version'] == 1, 'unknown/missing config fields or schema')
    for name, fields in FIELDS.items():
        require(set(cfg[name]) == fields, f'unknown/missing fields: {name}')
    for key in ('module_name', 'python_module'):
        require(re.fullmatch(r'[A-Za-z0-9_-]+/[A-Za-z0-9][A-Za-z0-9_.+-]*', cfg[key])
                and not re.search(r'REQUIRED|PLACEHOLDER|CHANGE_ME', cfg[key], re.I),
                f'{key} requires explicit name/version')
    require(cfg['module_name'].split('/')[0] != cfg['python_module'].split('/')[0], 'module names collide')
    prefix, modules = (absolute(cfg[k]) for k in ('release_prefix', 'module_root'))
    require(not prefix.exists() and not modules.exists(), 'fresh release_prefix AND module_root required; never overwrite')
    require(not overlap(prefix, modules), 'release/module overlap')
    inventory = inspect(cfg)
    repo = Path(__file__).resolve().parents[3]
    protected = [Path(p) for p in inventory['protected'] if p not in (str(prefix), str(modules))]
    protected += [repo, config_path]
    for dest in (prefix, modules):
        require(not any(overlap(dest, p) for p in protected), 'release/module/source/runtime/config overlap')
    # Everything above is read-only. Failed construction below preserves diagnostics;
    # a corrected attempt always needs two fresh destinations.
    prefix.mkdir(parents=True, mode=0o755)
    provenance = prefix / 'provenance'
    provenance.mkdir()
    state = {'status': 'building', 'config_sha256': digest(config_path),
             'assembler_sha256': digest(Path(__file__)), 'scope': inventory['scope']}
    statefile = provenance / 'build.json'
    try:
        (provenance / 'config.json').write_bytes(raw)
        (provenance / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
        lib, bin_dir = prefix / 'lib', prefix / 'bin'
        lib.mkdir()
        bin_dir.mkdir()
        dispatcher = lib / 'launcher.py'
        dispatcher.write_bytes(Path(__file__).with_name('launcher.py').read_bytes())
        for tool in ('myotally', 'imagej', 'cellprofiler', 'scanpy', 'adaptive-screen', 'doctor'):
            path = bin_dir / ('wagers-' + tool)
            path.write_text('#!/bin/sh\nset -eu\n'
                            'unset PYTHONPATH PYTHONHOME PYTHONUSERBASE PYTHONSTARTUP PYTHONINSPECT\n'
                            'export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1\n'
                            f'exec {shlex.quote(cfg["host_python"])} -I -B '
                            f'{shlex.quote(str(dispatcher))} {shlex.quote(tool)} "$@"\n')
            path.chmod(0o755)
        modules.mkdir(parents=True, mode=0o755)
        modulefile = modules / (cfg['module_name'] + '.lua')
        modulefile.parent.mkdir(parents=True, exist_ok=False)
        module_text = (
            'help([[Five Wagers software tutorials. Biological validation and user access pending.]])\n'
            'whatis("Wagers pinned runtime routes; read-only inventory: wagers-doctor")\n'
            f'depends_on({json.dumps(cfg["python_module"])})\n'
            f'prepend_path("PATH", {json.dumps(str(bin_dir))})\n'
            f'setenv("WAGERS_TOOLS_PREFIX", {json.dumps(str(prefix))})\n'
            f'setenv("WAGERS_TOOLS_MODULE", {json.dumps(cfg["module_name"])})\n')
        with modulefile.open('x') as stream:
            stream.write(module_text)
        state.update(status='assembled-not-installed-validated', modulefile=str(modulefile),
                     dispatcher_sha256=digest(dispatcher), module_sha256=digest(modulefile))
    except Exception as exc:
        state.update(status='failed', error=str(exc))
        raise
    finally:
        statefile.write_text(json.dumps(state, indent=2) + '\n')
    return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(assemble(args.config), indent=2))
    except (ValueError, OSError, KeyError, TypeError, SyntaxError) as exc:
        print(f'ASSEMBLY REFUSED: {exc}', file=sys.stderr)
        sys.exit(2)
