#/bin/bash

this_dir="`dirname "$0"`"
venv_dir="$this_dir/.venv"

if [ -d "$venv_dir" ]; then
    echo "Venv directory '$venv_dir' seems to exist. Exiting."
    exit
fi

echo "Creating environment"
python3 -m venv "$venv_dir"

source "$venv_dir/bin/activate"

echo "Installing requirements"
pip3 install -r "$this_dir/requirements.txt"
echo "Done."

