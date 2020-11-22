import time


import numpy
import scipy
import pandas
import django
import matplotlib


def handler(event):
    print("in function: ", event)
    return {
        "timestamp": int(round(time.time() * 1000000)),
        "data": event["key1"] + " " + event["key2"]
    }
