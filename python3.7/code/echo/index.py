import time


# import numpy
# import scipy
# import pandas
# import django
# import matplotlib


def handler(event):
    print("in function: ", event)
    return int(round(time.time() * 1000000))
