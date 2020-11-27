import importlib
import json
import os
import socket
import sys
import time
import traceback

import syscall


def exec_function(param):
    result = {
        "id": param["id"],
        "containerProcessRunAt": int(round(time.time() * 1000000))  # 记录服务启动时的时间
    }

    # 加载执行函数代码
    try:
        sys.path.append(param["codePath"])
        handler = importlib.import_module(param["handler"])
        result["functionRunTimestamp"] = int(round(time.time() * 1000000))
        result["functionResult"] = handler.handler(param["params"])
    except Exception as e:
        traceback.format_exc()
        result["error"] = str(e)
    result["functionEndTimestamp"] = int(round(time.time() * 1000000))

    # # 上报结果
    # conn = http.client.HTTPConnection("127.0.0.1:" + param["servePort"])
    # conn.request("PUT", "/inner/function/end", json.dumps(result, default=lambda obj: obj.__dict__),
    #              {'content-type': "application/json"})

    print(param["id"], ",",
          result["containerProcessRunAt"] - param["containerCreateAt"], ",",
          result["functionRunTimestamp"] - result["containerProcessRunAt"], ",",
          result["functionRunTimestamp"] - param["containerCreateAt"])

    # 主动退出
    sys.exit(0)


def init_container(exec_ctx):
    t = exec_ctx["containerCreateAt"]
    exec_ctx["containerCreateAt"] = int(round(time.time() * 1000000))
    print("--> ", t, exec_ctx["containerCreateAt"])
    try:
        # unshare
        res = syscall.unshare()
        if res != 0:
            raise Exception("syscall.unshare return non zero status " + res)

        # # set cgroup
        # cur_pid = str(os.getpid())
        # for cgroup in param["cgroupFileList"]:
        #     f = open(cgroup, 'w')
        #     f.write(cur_pid)
        #     f.close()

        # chroot
        root_fd = os.open(exec_ctx["rootFsPath"], os.O_RDONLY)
        os.fchdir(root_fd)
        os.chroot(".")
        os.close(root_fd)

        # 记录容器进程启动时的时间
        process_start_time = int(round(time.time() * 1000000))

        # 创建容器进程
        pid = os.fork()
        if pid == 0:  # child, 正式进入容器环境中
            exec_function(exec_ctx)
        else:  # parent
            # 上报容器进程启动
            # conn = http.client.HTTPConnection("127.0.0.1:" + exec_ctx["servePort"])
            # conn.request("PUT", "/inner/process/run/" + exec_ctx["id"] + "/" + str(process_start_time) + "/" + str(pid))
            os.waitpid(pid, 0)
    except Exception as e:
        traceback.format_exc()
        print(e)

    # 上报容器进程退出, (wait返沪结果或者异常时)
    # conn = http.client.HTTPConnection("127.0.0.1:" + exec_ctx["servePort"])
    # conn.request("PUT", "/inner/process/end/" + exec_ctx["id"] + "/" + str(int(round(time.time() * 1000000))))

    sys.exit(0)  # 主动退出


# 开始监听指令
def start_fork_server(sock):
    header_len = 2
    msg_len = 0
    recv_data = "".encode("utf-8")
    while True:
        data = sock.recv(1024)
        recv_data += data

        # 未获取到消息长度，先获取长度
        if msg_len == 0:
            if len(recv_data) < header_len:  # 接收的不足2个字节，不足以获取消息的长度，继续接收
                continue
            else:  # 接收的消息足够获取消息的长度
                msg_len = int.from_bytes(recv_data[:header_len], byteorder='little', signed=True)  # 获取消息长度
                recv_data = recv_data[header_len:]  # 去掉消息长度头部

        # 现在确定已经拿到消息的长度了

        # 当前收到的数据小于期望的数据长度，继续接收
        if len(recv_data) < msg_len:
            continue

        # 当前收到的数据大于等于期望的数据长度，开始解析
        while len(recv_data) >= msg_len:
            message = recv_data[:msg_len]  # 拿到的消息
            recv_data = recv_data[msg_len:]  # 去掉已经接收的数据

            # 拿到数据以后，开始创建容器父进程
            exec_ctx = json.loads(message)
            ppid = os.fork()
            if ppid == 0:  # 子进程，即容器进程的父进程
                sock.close()
                init_container(exec_ctx)

            # 继续解析
            if len(recv_data) < header_len:
                msg_len = 0
                break
            msg_len = int.from_bytes(recv_data[:header_len], byteorder='little', signed=True)
            recv_data = recv_data[header_len:]


# 连接到 server 并注册自身
def register(process_id, sock_file):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(sock_file)
        sock.sendall((process_id + '\n').encode())
        return sock
    except Exception as e:
        traceback.format_exc()
        print("register error: ", e)
        sys.exit(-1)


# 预加载 package
def load_packages(package_set):
    for package in package_set:
        importlib.import_module(package)


zygote_param = json.loads(sys.argv[-1])
unix_sock = register(zygote_param["id"], zygote_param["serverSocketFile"])
load_packages(zygote_param["packageSet"])
start_fork_server(unix_sock)
