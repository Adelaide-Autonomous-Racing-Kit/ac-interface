#!/usr/bin/env bash
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
runtime="${AC_MPC_RUNTIME:-$(dirname -- "$(git -C "$here" rev-parse --path-format=absolute --git-common-dir)")/../ac-mpc-run}"
runtime="$(cd -- "$runtime" && pwd)"
source "$runtime/environment.sh"
if [[ -d "$here/build/private-xvfb/usr/bin" ]]; then
    export PATH="$here/build/private-xvfb/usr/bin:$PATH"
fi
export PYTHONPATH="$here/../../src${PYTHONPATH:+:$PYTHONPATH}"
exec "$runtime/.venv/bin/python" "$here/run.py" --runtime "$runtime" "$@"
