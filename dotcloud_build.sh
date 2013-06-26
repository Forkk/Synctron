#!/bin/sh
# Build script for dotcloud.

(cd $HOME ; [ ! -d venv ] && virtualenv --python=/usr/bin/python2.7 venv)

. $HOME/venv/bin/activate

pip install -r requirements.txt

cp -Rf * $HOME/
