#!/bin/bash
#git push --follow-tags
rm -rf dist
python2 setup.py sdist bdist_wheel
#python3 setup.py sdist bdist_wheel
twine upload dist/*
