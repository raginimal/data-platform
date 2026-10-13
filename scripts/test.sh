#!/usr/bin/env bash
set -euo pipefail

if test -d tests && find tests -type f -name 'test_*.py' -print -quit | grep -q .; then
  python -m pytest
else
  echo "No application tests configured in the technology-neutral core."
fi
