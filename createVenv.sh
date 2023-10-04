#/bin/bash

venv_dir="`dirname "$0"`/.venv"

if [ -d "$venv_dir" ]; then
    echo "Venv directory '$venv_dir' seems to exist. Exiting."
    exit
fi

python -m venv "$venv_dir"

source "$venv_dir/bin/activate"

pip install -r "$venv_dir/requirements.txt"

