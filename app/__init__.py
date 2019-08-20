import os
import signal
import sys


def my_signal_handler(*args):
    if os.environ.get('RUN_MAIN') == 'true':
        print('stopped'.upper())
    sys.exit(0)


signal.signal(signal.SIGINT, my_signal_handler)

