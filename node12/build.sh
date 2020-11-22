#!/bin/bash

image=node:12
name=node12

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
cp bootstrap.js ${name}/

# 拷贝 demo 代码
cp -r code ${name}

## 安装 demo 代码的依赖包
docker run -it --rm --privileged -v $PWD:/root ${image} bash -c \
  "chroot /root/${name} "
