#!/bin/bash

. "`dirname "$0"`/.venv/bin/activate"

cat | "`dirname "$0"`/.venv/bin/python3" "`dirname "$0"`/mail_filter.py" "$@"
