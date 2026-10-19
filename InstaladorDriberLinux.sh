#!/usr/bin/env bash
# Compatibility entry point retained from the original prototype.
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
exec bash "$script_dir/install-printer.sh" "$@"
