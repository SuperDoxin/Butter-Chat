# -*- coding: utf-8 -*-
import gi
from twisted.internet import gtk3reactor

gi.require_version("Gtk", "3.0")
gtk3reactor.install()
