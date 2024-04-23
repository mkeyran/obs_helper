#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo "exec">>/tmp/obsidian.log
cd $SCRIPT_DIR
poetry run python $SCRIPT_DIR/main.py "$@" >> /tmp/obsidian.log