#!/bin/sh

test -d "`dirname "$0"`/.venv" || python3 -m venv .venv
. "`dirname "$0"`/.venv/bin/activate"
pip3 install -r "`dirname "$0"`/requirements.txt"
