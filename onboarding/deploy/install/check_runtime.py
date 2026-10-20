"""Small installation probes; these are not tutorial or scientific acceptance suites."""
import importlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys

sys.dont_write_bytecode = True


def check(kind, recipe=None):
    expected_python = '3.10.14' if kind == 'myotally' else '3.12.12'
    if platform.python_version() != expected_python:
        raise ValueError('Python version mismatch: ' + platform.python_version())
    pins = {}
    if kind == 'myotally':
        pins = {'numpy': '1.24.4', 'scipy': '1.10.1', 'Pillow': '10.0.1'}
        for name in ('numpy', 'scipy', 'PIL.Image', 'cv2', 'tkinter'):
            importlib.import_module(name)
        import cv2
        if cv2.__version__ != '4.8.1':
            raise ValueError('OpenCV version mismatch')
    elif kind in ('scanpy', 'adaptive'):
        for line in Path(recipe).read_text().splitlines():
            if line and not line.startswith('#'):
                name, version = line.split('==')
                pins[name] = version
        for name in (('scanpy', 'anndata', 'numpy', 'scipy') if kind == 'scanpy'
                     else ('numpy', 'scipy', 'sklearn.gaussian_process')):
            importlib.import_module(name)
    elif kind != 'base':
        raise ValueError('unknown runtime probe')
    actual = {name: importlib.metadata.version(name) for name in pins}
    if actual != pins:
        raise ValueError('distribution pin mismatch: ' + repr(actual))
    return {'status': 'runtime-probe-passed', 'scope': 'versions/imports only; no tutorial acceptance',
            'python': platform.python_version(), 'executable': sys.executable,
            'prefix': sys.prefix, 'base_prefix': sys.base_prefix, 'versions': actual}


if __name__ == '__main__':
    print(json.dumps(check(*sys.argv[1:]), indent=2))
