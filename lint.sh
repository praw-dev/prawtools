#!/bin/bash

dir=$(dirname $0)

# flake8 (runs pycodestyle and pyflakes)
flake8 $dir/prawtools
if [ $? -ne 0 ]; then
    echo "Exiting due to flake8 errors. Fix and re-run to finish tests."
    exit $?
fi

# pylint
output=$(pylint --rcfile=$dir/.pylintrc $dir/prawtools 2> /dev/null)
if [ -n "$output" ]; then
    echo "--pylint--"
    echo -e "$output"
fi

# pydocstyle
find $dir/prawtools -name [A-Za-z_]\*.py | xargs pydocstyle

exit 0
