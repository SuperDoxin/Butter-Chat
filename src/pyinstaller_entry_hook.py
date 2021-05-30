# -*- coding: utf-8 -*-
from twisted.internet import default

# avoid pyinstaller installing the default reactor
default.install = lambda *args, **kwargs: None
