import http.client
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

    # 上报结果
    conn = http.client.HTTPConnection("127.0.0.1:" + param["servePort"])
    conn.request("PUT", "/inner/function/end", json.dumps(result, default=lambda obj: obj.__dict__),
                 {'content-type': "application/json"})

    # 主动退出
    sys.exit(0)


# def do_exec(param):
#     param["afterForkTime"] = time.time_ns()
#
#     # 加载函数包
#     sys.path.append(param["codePath"])
#     # chroot以后这些包会找不到，需要特殊处理
#     package_path = ['/usr/local/lib/python37.zip', '/usr/local/lib/python3.7',
#                     '/usr/local/lib/python3.7/lib-dynload', '/usr/local/lib/python3.7/site-packages']
#     for p in package_path:
#         sys.path.append(p)
#
#     result = {
#         "id": param["id"],
#     }
#     try:
#         handler = importlib.import_module(param["handler"])
#         result["result"] = handler.handler(param["event"])
#     except Exception as e:
#         traceback.format_exc()
#         result["error"] = e
#
#     param["afterHandlerTime"] = time.time_ns()
#
#     # TODO 结果写回 server
#     print("firstFork=" + str((param["afterFirstForkTime"] - param["startTime"]) / 1e6) + ", " +
#           "unshare=" + str((param["afterUnshareTime"] - param["afterFirstForkTime"]) / 1e6) + ", " +
#           "chroot=" + str((param["afterChrootTime"] - param["afterUnshareTime"]) / 1e6) + ", " +
#           "fork=" + str((param["afterForkTime"] - param["afterChrootTime"]) / 1e6) + ", " +
#           "handler=" + str((param["afterHandlerTime"] - param["afterForkTime"]) / 1e6) + ", " +
#           "total=" + str((param["afterHandlerTime"] - param["afterFirstForkTime"]) / 1e6)
#           )
#
#     sys.exit(0)


def new_container(exec_ctx):
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

        # fork
        pid = os.fork()
        if pid == 0:  # child, 正式进入容器环境中
            exec_function(exec_ctx)
        else:  # parent
            # 上报容器进程启动
            conn = http.client.HTTPConnection("127.0.0.1:" + exec_ctx["servePort"])
            conn.request("PUT", "/inner/process/run/" + exec_ctx["id"] + "/" + str(process_start_time) + "/" + str(pid))
            os.waitpid(pid, 0)
    except Exception as e:
        traceback.format_exc()
        print(e)

    # 上报容器进程退出, (wait返沪结果或者异常时)
    conn = http.client.HTTPConnection("127.0.0.1:" + exec_ctx["servePort"])
    conn.request("PUT", "/inner/process/end/" + exec_ctx["id"] + "/" + str(int(round(time.time() * 1000000))))

    sys.exit(0)  # 主动退出


# 开始监听指令
def start_fork_server(sock):
    while True:
        data = sock.recv(1024)
        print(str(data))
        exec_ctx = json.loads(data)
        print(exec_ctx)
        ppid = os.fork()
        if ppid == 0:  # 子进程
            sock.close()
            new_container(exec_ctx)


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
