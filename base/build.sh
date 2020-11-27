#!/bin/bash

if [ $# != 1 ]; then
  echo "USAGE: build.sh WorkspacePath"
  exit 1
fi

image=python:3.7
name=base
workspace=$1

# generate rootfs
containerId=$(docker run -d ${image})
mkdir ${name} &&
  (docker export "${containerId}" | tar -C ${name} -xvf -) &&
  docker rm -f "${containerId}"

# set dns
cat >${name}/etc/resolv.conf <<EOF
nameserver 223.5.5.5
nameserver 223.6.6.6
nameserver 8.8.8.8
EOF

# 构建 pause
docker run -it -v $PWD:/go/src golang:1.14 bash -c "cd /go/src && go build -o pause pause.go"
mv pause ${name}/bin/

# 拷贝 rootfs 到 workspace
if [ ! -d "${workspace}/runtime" ]; then
  mkdir -p "${workspace}"/runtime
fi
mv ${name} "${workspace}"/runtime/
