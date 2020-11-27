import time


import django


def handler(event):
    return {
        "timestamp": int(round(time.time() * 1000000)),
        "data": event["key1"] + " " + event["key2"]
    }
