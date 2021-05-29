# -*- coding: utf-8 -*-
import zlib

from . import versions  # noqa nosort
from gi.repository import Gdk  # noqa nosort
from gi.repository import Gtk  # noqa nosort


def add_css_class(widget, class_):
    context = widget.get_style_context()
    context.add_class(class_)


class ChannelList(Gtk.StackSwitcher):
    def __init__(self):
        Gtk.StackSwitcher.__init__(self)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        add_css_class(self, "channel-switcher")


class ChannelStack(Gtk.Stack):
    def __init__(self):
        Gtk.Stack.__init__(self)
        self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)


class Message(Gtk.VBox):
    def __init__(self, author, message):
        Gtk.HBox.__init__(self)
        self.set_hexpand(False)
        add_css_class(self, "message")
        self.props.halign = Gtk.Align.START

        author_label = Gtk.Label(label=author)
        author_label.set_xalign(0)
        add_css_class(author_label, "author")
        add_css_class(author_label, self._name_to_color_class(author))
        self.pack_start(author_label, False, False, 0)

        message_label = Gtk.Label(label=message)
        message_label.set_xalign(0)
        message_label.set_line_wrap(True)
        add_css_class(message_label, "message-label")
        self.pack_start(message_label, False, False, 0)

    def _name_to_color_class(self, author):
        hue = zlib.crc32(author.encode("utf-8")) * 90 // 0xFFFFFFFF * 4
        return f"label_color_h{hue:02d}"


class MessageList(Gtk.VBox):
    def add_message(self, author, message):
        message = Message(author, message)
        self.pack_start(message, False, False, 0)


class Channel(Gtk.VBox):
    def __init__(self):
        Gtk.VBox.__init__(self)

        topic = Gtk.Label(label="No topic set.")
        topic.set_line_wrap(True)
        topic.set_justify(Gtk.Justification.LEFT)
        topic.set_xalign(0)
        add_css_class(topic, "topic")
        self.pack_start(topic, False, False, 0)

        vbox = Gtk.VBox()
        self.pack_start(vbox, True, True, 0)

        message_list = MessageList()
        vbox.pack_start(message_list, True, True, 0)
        message_list.add_message(
            "simtr",
            "My internet is down, and the only think I can connect to is libera for some reason.",
        )
        message_list.add_message("savask", "No idea")
        message_list.add_message("Ristovski", "savask: rofl")

        text_entry = Gtk.Entry()
        text_entry.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, "go-next-symbolic"
        )
        text_entry.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, True)
        text_entry.set_icon_sensitive(Gtk.EntryIconPosition.SECONDARY, True)
        self.pack_start(text_entry, False, False, 0)


class ChatWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Butter")
        self.set_default_size(600, 400)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_path("src/style.css")  # TODO: autodetect this path
        screen = Gdk.Screen.get_default()
        style_context = self.get_style_context()
        style_context.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.props.title = "Butter"
        self.set_titlebar(header)

        hbox = Gtk.HBox()
        self.add(hbox)

        channel_list = ChannelList()
        hbox.pack_start(channel_list, False, False, 0)

        channel_stack = ChannelStack()
        hbox.pack_start(channel_stack, True, True, 10)

        channel_stack.add_titled(Channel(), "#powder", "#powder")
        channel_stack.add_titled(Gtk.Label(label="Bar"), "bar", "Bar")
        channel_stack.add_titled(Gtk.Label(label="Baz"), "baz", "Baz")
        channel_list.set_stack(channel_stack)


w = ChatWindow()
w.connect("destroy", Gtk.main_quit)  #  TODO: minimize to tray?
w.show_all()

Gtk.main()
