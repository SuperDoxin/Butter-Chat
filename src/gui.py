# -*- coding: utf-8 -*-
import re
import zlib

from . import protocol

from . import versions  # noqa nosort
from gi.repository import Gdk  # noqa nosort
from gi.repository import GLib  # noqa nosort
from gi.repository import GObject  # noqa nosort
from gi.repository import Gtk  # noqa nosort


def markup_urls(text):
    output = []
    matches = re.finditer(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        text,
    )
    offset = 0
    for m in matches:
        print(offset, m.start())
        output.append(GLib.markup_escape_text(text[offset : m.start()]))
        escaped_url = GLib.markup_escape_text(m[0])
        output.append('<a href="' + escaped_url + '">' + escaped_url + "</a>")
        offset = m.end()
    output.append(GLib.markup_escape_text(text[offset:]))
    return "".join(output)


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

        message_label = Gtk.Label()
        message_label.set_markup(markup_urls(message))
        message_label.set_xalign(0)
        message_label.set_line_wrap(True)
        message_label.set_selectable(True)
        add_css_class(message_label, "message-label")
        self.pack_start(message_label, False, False, 0)

    def _name_to_color_class(self, author):
        hue = zlib.crc32(author.encode("utf-8")) * 90 // 0xFFFFFFFF * 4
        return f"label_color_h{hue:02d}"


class MessageList(Gtk.VBox):
    def add_message(self, author, message):
        message = Message(author, message)
        self.pack_start(message, False, False, 0)
        message.show_all()


class Channel(Gtk.VBox):
    def __init__(self, host, port, channel):
        Gtk.VBox.__init__(self)
        self.host = host
        self.port = port
        self.channel = channel

        self.topic = Gtk.Label(label="No topic set.")
        self.topic.set_line_wrap(True)
        self.topic.set_justify(Gtk.Justification.LEFT)
        self.topic.set_xalign(0)
        add_css_class(self.topic, "topic")
        self.pack_start(self.topic, False, False, 0)

        vbox = Gtk.VBox()
        self.pack_start(vbox, True, True, 0)

        self.message_list = MessageList()
        vbox.pack_start(self.message_list, True, True, 0)

        text_entry = Gtk.Entry()
        text_entry.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, "go-next-symbolic"
        )
        text_entry.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, True)
        text_entry.set_icon_sensitive(Gtk.EntryIconPosition.SECONDARY, True)
        text_entry.connect("activate", self.send_message)
        self.pack_start(text_entry, False, False, 0)

    def on_message_received(self, user, message):
        self.message_list.add_message(user, message)

    def send_message(self, widget):
        protocol.send_message(self.host, self.port, self.channel, widget.get_text())
        widget.set_text("")

    def on_topic_changed(self, topic):
        if topic:
            self.topic.set_markup(markup_urls(topic))
        else:
            self.topic.set_text("No topic set.")


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

        self.channel_stack = ChannelStack()
        hbox.pack_start(self.channel_stack, True, True, 10)

        channel_list.set_stack(self.channel_stack)

        protocol.register_handler("channel_joined", self.on_channel_joined)
        protocol.register_handler("message_received", self.on_message_received)
        protocol.register_handler("topic_changed", self.on_topic_changed)

        protocol.connect("butter-client", "irc.libera.chat")

    def on_channel_joined(self, *, channel, host, port):
        channel_id = f"{host}:{port}/{channel}"
        channel_widget = Channel(host, port, channel)
        channel_widget.show_all()
        self.channel_stack.add_titled(channel_widget, channel_id, channel)

    def on_message_received(self, *, user, message, channel, host, port):
        channel_id = f"{host}:{port}/{channel}"
        channel_widget = self.channel_stack.get_child_by_name(channel_id)
        if channel_widget:
            channel_widget.on_message_received(user, message)

    def on_topic_changed(self, *, topic, channel, host, port):
        channel_id = f"{host}:{port}/{channel}"
        channel_widget = self.channel_stack.get_child_by_name(channel_id)
        if channel_widget:
            channel_widget.on_topic_changed(topic)
