import time


def handler(event):
    result = ""
    for key in event:
        result += event[key] + " "
    return {
        "timestamp": int(round(time.time() * 1000000)),
        "data": result
    }
