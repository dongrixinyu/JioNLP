#!/bin/bash

# make sure your python path is like the below ones.
# python: /home/ubuntu/anaconda3/bin/python
# working in the directory with `setup.py` file.

jionlp_version="1.4.7"

if [ -d build ]; then
    rm -rf build
fi
if [ -d jiojio.egg-info ]; then
    rm -rf jiojio.egg-info
fi

python3 setup.py bdist_wheel --universal

pip install twine
twine upload dist/jionlp-${jiojio_version}*whl

echo "finished!"
exit 0
