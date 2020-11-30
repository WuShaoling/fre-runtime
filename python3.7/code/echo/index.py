import time


def handler(event):
    result = 0
    for key in event:
        result += event[key]
    return {
        "timestamp": int(round(time.time() * 1000000)),
        "data": result
    }
