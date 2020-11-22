#!/bin/bash

image=python:3.7
name=python3.7
workspace=../../engine/workspace

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

# 拷贝 demo 代码
cp -r code ${name}

# 拷贝 zygote 相关文件
if [ ! -d "${workspace}/zygote/python3.7" ]; then
  mkdir -p ${workspace}/zygote/python3.7
fi
cp -r zygote ${workspace}/zygote/python3.7

## 安装 demo 代码的依赖包
docker run -it --rm --privileged -v $PWD:/root ${image} bash -c \
  "chroot /root/${name} pip3 install -i http://pypi.douban.com/simple --trusted-host pypi.douban.com scipy numpy pandas django matplotlib"
