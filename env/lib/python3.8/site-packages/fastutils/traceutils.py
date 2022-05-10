"""
failed for complex application.
"""

import os
import sys
import time
import logging
import pathlib
import threading
from magic_import import import_from_string

logger = logging.getLogger(__name__)

trace_message_sep = ","

traced_folders = set()
traced_files = set()

def set_trace_message_sep(sep=","):
    global trace_message_sep
    trace_message_sep = sep

def register_trace_modules(*module_names):
    for module_name in module_names:
        module = import_from_string(module_name)
        if module:
            filename = module.__file__
            if filename.endswith("__init__.py"):
                traced_folders.add(pathlib.Path(os.path.abspath(os.path.dirname(filename))))
            else:
                traced_files.add(pathlib.Path(filename))

register_trace_modules("__main__")

def trace_calls(frame, event, arg):
    if not event in ["call", "c_call"]:
        return
    if not os:
        return False
    if not os.getpid:
        return False
    if not threading:
        return False
    if not threading.get_ident:
        return False
    if not time:
        return
    if not time.time:
        return
    if not logger:
        return
    if not logger.info:
        return
    info = {
        "id": id(frame),
        "process": os.getpid(),
        "thread": threading.get_ident(),
        "ts": time.time(),
    }
    if frame.f_back:
        info["pid"] = id(frame.f_back)
    else:
        info["pid"] = None
    if frame.f_code:
        info["filename"] = str(frame.f_code.co_filename)
        info["function"] = frame.f_code.co_name
    else:
        info["filename"] = None
        info["function"] = None
    msg = "{process}{trace_message_sep}{thread}{trace_message_sep}{id}{trace_message_sep}{pid}{trace_message_sep}{filename}{trace_message_sep}{function}{trace_message_sep}{ts}".format(trace_message_sep=trace_message_sep, **info)
    if pathlib.Path(info["filename"]) in traced_files:
        logger.info(msg)
        return
    else:
        file_parents = list(pathlib.Path(info["filename"]).parents)
        for folder in traced_folders:
            if folder in file_parents:
                logger.info(msg)
                return

def setup_trace(logger_name=None):
    if logger_name:
        global logger
        logger = logging.getLogger(logger_name)
    sys.settrace(trace_calls)
