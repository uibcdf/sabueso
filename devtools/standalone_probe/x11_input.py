"""Deliver bounded native input to this experiment's private Xvfb display only."""

import ctypes
import json
import os
import sys

event = json.loads(sys.argv[1])
if event["display"] != os.environ["DISPLAY"] or not event["display"].startswith(":"):
    raise SystemExit("Unexpected experiment display")
xlib = ctypes.CDLL("libX11.so.6")
xtest = ctypes.CDLL("libXtst.so.6")
xlib.XOpenDisplay.argtypes = [ctypes.c_char_p]
xlib.XOpenDisplay.restype = ctypes.c_void_p
xlib.XFlush.argtypes = [ctypes.c_void_p]
xlib.XCloseDisplay.argtypes = [ctypes.c_void_p]
display = xlib.XOpenDisplay(event["display"].encode())
if not display:
    raise SystemExit("Owned X display is unavailable")
try:
    if event["kind"] == "click":
        x, y = round(event["x"]), round(event["y"])
        if not (0 <= x < 1600 and 0 <= y < 1000):
            raise ValueError("Input outside the fixed experiment viewport")
        xtest.XTestFakeMotionEvent.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_ulong,
        ]
        xtest.XTestFakeButtonEvent.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_int,
            ctypes.c_ulong,
        ]
        xtest.XTestFakeMotionEvent(display, -1, x, y, 0)
        xtest.XTestFakeButtonEvent(display, 1, 1, 0)
        xtest.XTestFakeButtonEvent(display, 1, 0, 0)
    elif event["kind"] == "enter":
        xlib.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        xlib.XKeysymToKeycode.restype = ctypes.c_uint
        xtest.XTestFakeKeyEvent.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_int,
            ctypes.c_ulong,
        ]
        code = xlib.XKeysymToKeycode(display, 0xFF0D)
        xtest.XTestFakeKeyEvent(display, code, 1, 0)
        xtest.XTestFakeKeyEvent(display, code, 0, 0)
    else:
        raise ValueError("Unknown native input")
    xlib.XFlush(display)
finally:
    xlib.XCloseDisplay(display)
