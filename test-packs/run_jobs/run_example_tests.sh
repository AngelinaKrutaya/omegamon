#!/bin/bash -l
IN_TESTPACK=$(dirname $BASH_SOURCE)
SEARCHPATH=$IN_TESTPACK/../tests/
MARKER='example'

. $HOME/venv/bin/activate
taf -v
cd $SEARCHPATH
pytest -m "$MARKER"
