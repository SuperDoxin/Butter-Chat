# -*- coding: utf-8 -*-
import os
import os.path
import sys

from .gui import ChatWindow

from . import versions  # noqa nosort
from . import protocol  # noqa nosort


def main():
    if getattr(sys, "frozen", False):
        os.chdir(os.path.dirname(os.path.realpath(sys.executable)))
    else:
        os.chdir(os.path.dirname(os.path.realpath(__file__)))

    w = ChatWindow()
    w.connect("destroy", lambda e: protocol.stop())  #  TODO: minimize to tray?
    w.show_all()

    protocol.start()
