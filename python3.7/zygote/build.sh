#!/bin/bash

# build clibs
docker run -it --rm \
  -v "$PWD":/root python:3.7 \
  bash -c "cd /root && python3 setup.py build_ext --inplace && rm -rf build && mv *.so syscall.so"
