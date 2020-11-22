# fre-runtime

fre 基础运行时环境，目录名即为运行时环境名 ${runtime_name}

## runtime 子目录说明

以 python3.7 为例：

- code: demo 代码目录，构建时拷贝到 rootfs 的 /code 目录，/code/ 下的每个目录为一个应用
- zygote: 对于支持 zygote 的语言，该目录存放该语言的 zygote 相关的代码，构建时拷贝到 workspace/zygote/${runtime_name} 目录下，对于不支持 zygote 的语言(node)，该目录为空即可
- bootstrap.py: 函数的执行器，拷贝到 rootfs 的 / 目录
- build.sh: rootfs 构建脚本
- 构建完成后，rootfs 会拷贝到 workspace/runtime/${runtime_name}
