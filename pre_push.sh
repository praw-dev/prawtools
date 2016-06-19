#!/bin/sh

function exit_error() {
    echo $1
    exit 1
}

python setup.py test || exit_error "Please fix test issues."
echo "tests pass!"

flake8 --version > /dev/null 2>&1
if [ $? -ne 0 ]; then
    exit_error "Please install flake8: pip install flake8"
fi
flake8 || exit_error "Please correct flake8 issues."
echo "style pass!"

pydocstyle --version > /dev/null 2>&1
if [ $? -ne 0 ]; then
    exit_error "Please install pydocstyle: pip install pydocstyle"
fi
pydocstyle || exit_error "Please correct pydocstyle issues."
echo "doc style pass!"

exit 0
