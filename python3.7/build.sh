#!/bin/bash

if [ $# != 1 ]; then
  echo "USAGE: build.sh WorkspacePath"
  exit 1
fi

image=python:3.7
name=python3.7
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

# 拷贝 bootstrap.py
cp bootstrap.py ${name}/

################# demo 代码 #################
# 拷贝 demo 代码
cp -r code ${name}

## 安装 demo 代码的依赖包
docker run -it --rm --privileged -v "$PWD":/root ${image} bash -c \
  "chroot /root/${name} pip3 install -i http://pypi.douban.com/simple --trusted-host pypi.douban.com scipy numpy pandas django matplotlib"

################# zygote 相关 #################
# build
cd zygote && sh build.sh && cd ..

# 拷贝 zygote 相关文件
if [ ! -d "${workspace}/zygote" ]; then
  mkdir -p "${workspace}"/zygote
fi
cp -r zygote "${workspace}"/zygote/${name}

# 拷贝 rootfs 到 workspace
if [ ! -d "${workspace}/runtime" ]; then
  mkdir -p "${workspace}"/runtime
fi
mv ${name} "${workspace}"/runtime/
