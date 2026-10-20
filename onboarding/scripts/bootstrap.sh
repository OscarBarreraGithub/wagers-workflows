#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 1 ]]; then
  echo 'Usage: bash scripts/bootstrap.sh /absolute/deploy-config.json' >&2
  exit 2
fi
# Run from a site shell where Lmod is initialized. No shell-startup modifications.
module load python
exec python -B "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/bootstrap.py" --config "$1"
