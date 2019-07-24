#!/bin/bash
cmd='python3 -m flake8 . --count --exclude=./.*,./venv,./build --select=E9,F63,F7,F82 --show-source --statistics'
echo -e "Checking for python errors:\n  ${cmd}"
${cmd}
