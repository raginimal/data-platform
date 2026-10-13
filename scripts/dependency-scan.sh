#!/usr/bin/env bash
# Python overlay scanner for ARCH-DEP-004; selected via DEPENDENCY_SCANNER.
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root_dir"

pip-audit -r requirements.txt
