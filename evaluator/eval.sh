#!/usr/bin/env bash
# Evaluate R0 or a submitted DEF/Verilog pair. No Resizer is run here.
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
for arg in "$@"; do
    if [[ "$arg" == --reference-resizer* ]]; then
        echo 'Resizer optimization is not part of public evaluation.' >&2
        exit 2
    fi
done
exec "${PYTHON_EXE:-python3}" "$root/run.py" "$@"
