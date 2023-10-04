#/bin/bash

this_dir="`dirname "$0"`"
venv_dir="$this_dir/.venv"

if [ -d "$venv_dir" ]; then
    echo "Venv directory '$venv_dir' seems to exist. Exiting."
    exit
fi

python3 -m venv "$venv_dir"

source "$venv_dir/bin/activate"

pip3 install -r "$this_dir/requirements.txt"

