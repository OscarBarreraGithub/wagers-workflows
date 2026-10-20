"""Create a fresh Python 3.12 venv; never alter an existing environment."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
import venv

sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
from workflow import PACKAGE, no_symlinks, protected_destination, write_json


def reserve_prefix(prefix):
    root = no_symlinks(prefix)
    # The legacy default is the sole allowed runtime inside the source package.
    if root != PACKAGE / '.runtime':
        protected_destination(root)
        if root.is_relative_to(PACKAGE):
            raise ValueError('external runtime prefix must be outside the source package')
    if root.exists():
        raise ValueError('runtime prefix already exists; select a fresh prefix; never overwrite an environment')
    root.parent.mkdir(parents=True, exist_ok=True)
    root.mkdir(mode=0o700)
    return root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', type=Path, default=PACKAGE / '.runtime')
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        raise SystemExit('Use Python 3.12 (tested patch: 3.12.12); do not use a system pip install.')
    try:
        root = reserve_prefix(args.prefix)
    except (ValueError, OSError) as exc:
        raise SystemExit(f'REFUSED runtime prefix: {exc}') from exc
    # Failures leave an inspectable incomplete runtime. Never remove/reuse it silently.
    metadata = {}
    for name, version in [('scanpy', '1.12.4'), ('anndata', '0.13.4')]:
        url = f'https://pypi.org/pypi/{name}/{version}/json'
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.load(response)
        metadata[name] = {'version': data['info']['version'], 'requires_python': data['info']['requires_python'],
                          'source': url}
    write_json(root / 'primary-metadata.json', metadata)
    venv.create(root, with_pip=True)
    py = root / 'bin/python'
    command = [str(py), '-B', '-m', 'pip', '--isolated', 'install', '--disable-pip-version-check',
               '--no-cache-dir', '--only-binary=:all:', '--index-url', 'https://pypi.org/simple',
               '--report', str(root / 'install-report.json'), '-r', str(PACKAGE / 'requirements.lock')]
    with (root / 'install.log').open('w') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        subprocess.run([str(py), '-B', '-m', 'pip', 'check'], stdout=log, stderr=subprocess.STDOUT, check=True)
    print(f'Runtime ready: {root}. Use its bin/python -B with --runtime-prefix and a fresh --output.')


if __name__ == '__main__':
    main()
