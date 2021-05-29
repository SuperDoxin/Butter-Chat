# -*- coding: utf-8 -*-
from .gui import ChatWindow

from . import versions  # noqa nosort
from . import protocol  # noqa nosort

w = ChatWindow()
w.connect("destroy", lambda e: protocol.stop())  #  TODO: minimize to tray?
w.show_all()

protocol.start()
