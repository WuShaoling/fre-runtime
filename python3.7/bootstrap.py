import http.client
import importlib
import json
import sys
import time
import traceback


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


# 解析参数
exec_ctx = json.loads(sys.argv[-1])
exec_function(exec_ctx)
