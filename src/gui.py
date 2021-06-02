# -*- coding: utf-8 -*-
import re

from . import protocol
from .identicon import get_identicon
from .identicon import name_to_color
from .identicon import name_to_color_class
from .namegen import generate_name

from . import versions  # noqa nosort
from gi.repository import Gdk  # noqa nosort
from gi.repository import GLib  # noqa nosort
from gi.repository import GObject  # noqa nosort
from gi.repository import Gtk  # noqa nosort


def markup_names(text, names, additional_markup=GLib.markup_escape_text):
    output = []
    regex = "|".join(re.escape(name) for name in names)
    matches = re.finditer(regex, text)
    offset = 0
    for m in matches:
        output.append(additional_markup(text[offset : m.start()]))
        escaped_name = GLib.markup_escape_text(m[0])
        color = name_to_color(m[0])
        output.append('<span color="' + color + '">' + escaped_name + "</span>")
        offset = m.end()
    output.append(additional_markup(text[offset:]))
    return "".join(output)


def markup_urls(text, additional_markup=GLib.markup_escape_text):
    output = []
    matches = re.finditer(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        text,
    )
    offset = 0
    for m in matches:
        output.append(additional_markup(text[offset : m.start()]))
        escaped_url = GLib.markup_escape_text(m[0])
        output.append('<a href="' + escaped_url + '">' + escaped_url + "</a>")
        offset = m.end()
    output.append(additional_markup(text[offset:]))
    return "".join(output)


def add_css_class(widget, class_):
    context = widget.get_style_context()
    context.add_class(class_)


class ChannelList(Gtk.StackSwitcher):
    # TODO: make me collapsible
    def __init__(self):
        Gtk.StackSwitcher.__init__(self)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        add_css_class(self, "channel-switcher")


class ChannelStack(Gtk.Stack):
    def __init__(self):
        Gtk.Stack.__init__(self)
        self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)


class Message(Gtk.HBox):
    def __init__(self, author, message, names):
        Gtk.HBox.__init__(self)

        add_css_class(self, "message")

        profile_image = Gtk.Image.new_from_pixbuf(get_identicon(author))
        profile_image.set_size_request(32, 32)
        profile_image.props.valign = Gtk.Align.END
        self.pack_start(profile_image, False, False, 0)

        vbox = Gtk.VBox()
        self.pack_start(vbox, True, True, 0)

        vbox.set_hexpand(False)
        add_css_class(vbox, "content")
        vbox.props.halign = Gtk.Align.START

        author_label = Gtk.Label(label=author)
        author_label.set_xalign(0)
        add_css_class(author_label, "author")
        add_css_class(author_label, name_to_color_class(author))
        vbox.pack_start(author_label, False, False, 0)

        message_label = Gtk.Label()
        message_label.set_markup(
            markup_urls(message, lambda text: markup_names(text, names))
        )
        message_label.set_xalign(0)
        message_label.set_line_wrap(True)
        message_label.set_selectable(True)
        add_css_class(message_label, "message-label")
        vbox.pack_start(message_label, False, False, 0)


class Action(Gtk.HBox):
    def __init__(self, author, message, names):
        Gtk.HBox.__init__(self)
        add_css_class(self, "action")

        message_label = Gtk.Label()
        message_label.set_markup(
            markup_urls(author + " " + message, lambda text: markup_names(text, names))
        )
        message_label.set_xalign(0)
        message_label.set_line_wrap(True)
        message_label.set_selectable(True)
        add_css_class(message_label, "message-label")
        self.pack_start(message_label, False, False, 0)


class Notice(Gtk.HBox):
    def __init__(self, author, message, names, error=False):
        Gtk.HBox.__init__(self)
        add_css_class(self, "notice")
        if error:
            add_css_class(self, "error")

        if author:
            message = author + ": " + message

        message_label = Gtk.Label()
        message_label.set_markup(
            markup_urls(message, lambda text: markup_names(text, names))
        )
        message_label.set_xalign(0)
        message_label.set_line_wrap(True)
        message_label.set_selectable(True)
        add_css_class(message_label, "message-label")
        self.pack_start(message_label, False, False, 0)


class MessageList(Gtk.VBox):
    def add_message(self, author, message, names):
        message = Message(author, message, names)
        self.pack_start(message, False, False, 0)
        message.show_all()

    def add_action(self, author, message, names):
        message = Action(author, message, names)
        self.pack_start(message, False, False, 0)
        message.show_all()

    def add_notice(self, author, message, names):
        message = Notice(author, message, names)
        self.pack_start(message, False, False, 0)
        message.show_all()

    def add_error(self, message, names):
        message = Notice(None, message, names, error=True)
        self.pack_start(message, False, False, 0)
        message.show_all()


class MessageEntry(Gtk.Entry):
    def __init__(self):
        Gtk.Entry.__init__(self)
        self.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, "go-next-symbolic"
        )
        self.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, True)
        self.set_icon_sensitive(Gtk.EntryIconPosition.SECONDARY, True)

        self.completion = Gtk.EntryCompletion()
        self.completion.set_match_func(self.match, None)
        self.completion.connect("match-selected", self.on_match)
        self.set_completion(self.completion)

        self.list_store = Gtk.ListStore(GObject.TYPE_STRING)
        self.completion.set_model(self.list_store)
        self.completion.set_text_column(0)

    def set_completions(self, completions):
        self.list_store.clear()
        for completion in completions:
            self.list_store.append((completion,))

    def match(self, completion, key, tree_iter, data):
        model = self.completion.get_model()
        completion_string = model[tree_iter][0]

        if " " in key:
            key = key.split(" ")[-1]

        return completion_string.lower().startswith(key.lower())

    def on_match(self, completion, model, tree_iter):
        # TODO: deal with the cursor not being at the end of the line better

        text = self.get_text()
        if " " in text:
            text = text.rpartition(" ")[0] + " "
            suffix = " "
        else:
            text = ""
            suffix = ": "

        text += model[tree_iter][0] + suffix
        self.set_text(text)
        self.set_position(-1)

        return True


class Channel(Gtk.VBox):
    def __init__(self, host, port, channel):
        Gtk.VBox.__init__(self)
        self.host = host
        self.port = port
        self.channel = channel
        self.names = []
        self._names = []

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

        self.text_entry = MessageEntry()
        self.text_entry.connect("activate", self.send_message)
        self.text_entry.set_completions(self.names)
        self.pack_start(self.text_entry, False, False, 0)

    def send_command(self, command, args):
        if command == "say":
            protocol.send_message(self.host, self.port, self.channel, args)
        elif command == "me":
            if not args:
                return
            protocol.send_action(self.host, self.port, self.channel, args)
        else:
            self.message_list.add_error(f'Unknown command "{command}"', [])

    def on_list_names(self, names):
        self._names.extend(names)

    def on_end_names(self):
        self.names = self._names
        self.text_entry.set_completions(self.names)
        self._names = []

    def on_message_received(self, user, message):
        self.message_list.add_message(user, message, self.names)

    def on_action_received(self, user, message):
        self.message_list.add_action(user, message, self.names)

    def on_notice_received(self, user, message):
        self.message_list.add_notice(user, message, self.names)

    def send_message(self, widget, do_command=True):
        text = widget.get_text()
        if not text:
            return
        if text[0] == "/":
            splat = text[1:].split(" ", 1)
            if len(splat) == 1:
                splat.append("")
            self.send_command(*splat)
        else:
            protocol.send_message(self.host, self.port, self.channel, text)
        widget.set_text("")

    def on_topic_changed(self, topic):
        if topic:
            self.topic.set_markup(markup_urls(topic))
        else:
            self.topic.set_text("No topic set.")

    def on_user_joined(self, user):
        self.names.append(user)
        self.text_entry.set_completions(self.names)

    def on_user_left(self, user):
        self.names.remove(user)
        self.text_entry.set_completions(self.names)

    def on_user_renamed(self, old_user, new_user):
        if old_user in self.names:
            self.names.remove(old_user)
            self.names.append(new_user)
        self.text_entry.set_completions(self.names)


class ChatWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Butter")
        self.set_default_size(600, 400)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_path("style.css")
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
        protocol.register_handler("action_received", self.on_action_received)
        protocol.register_handler("notice_received", self.on_notice_received)
        protocol.register_handler("topic_changed", self.on_topic_changed)
        protocol.register_handler("user_joined", self.on_user_joined)
        protocol.register_handler("user_left", self.on_user_left)
        protocol.register_handler("user_renamed", self.on_user_renamed)
        protocol.register_handler("list_names", self.on_list_names)
        protocol.register_handler("end_names", self.on_end_names)

        protocol.connect(generate_name(), "irc.libera.chat")

    def get_channel_widget(self, channel, host, port, create=False):
        channel_id = f"{host}:{port}/{channel}"
        channel_widget = self.channel_stack.get_child_by_name(channel_id)
        if create and not channel_widget:
            channel_widget = Channel(host, port, channel)
            channel_widget.show_all()
            self.channel_stack.add_titled(channel_widget, channel_id, channel)
        return channel_widget

    def on_list_names(self, *, channel, names, host, port):
        channel_widget = self.get_channel_widget(channel, host, port)
        if channel_widget:
            channel_widget.on_list_names(names)

    def on_end_names(self, *, channel, host, port):
        channel_widget = self.get_channel_widget(channel, host, port)
        if channel_widget:
            channel_widget.on_end_names()

    def on_channel_joined(self, *, channel, host, port):
        channel_id = f"{host}:{port}/{channel}"
        channel_widget = Channel(host, port, channel)
        channel_widget.show_all()
        self.channel_stack.add_titled(channel_widget, channel_id, channel)
        self.channel_stack.set_visible_child(channel_widget)

    def on_message_received(self, *, user, message, channel, host, port):
        channel_widget = self.get_channel_widget(channel, host, port, True)
        channel_widget.on_message_received(user, message)

    def on_action_received(self, *, user, message, channel, host, port):
        channel_widget = self.get_channel_widget(channel, host, port, True)
        channel_widget.on_action_received(user, message)

    def on_notice_received(self, *, user, message, channel, host, port):
        channel_widget = self.get_channel_widget(channel, host, port, True)
        channel_widget.on_notice_received(user, message)

    def on_topic_changed(self, *, topic, channel, host, port):
        channel_widget = self.get_channel_widget(channel, host, port)
        if channel_widget:
            channel_widget.on_topic_changed(topic)

    def on_user_joined(self, *, user, channel, host, port):
        channel_widget = self.get_channel_widget(channel, host, port)
        if channel_widget:
            channel_widget.on_user_joined(user)

    def on_user_left(self, *, user, channel, host, port):
        channel_widget = self.get_channel_widget(channel, host, port)
        if channel_widget:
            channel_widget.on_user_left(user)

    def on_user_renamed(self, *, old_user, new_user, host, port):
        for channel_widget in self.channel_stack.get_children():
            if channel_widget.host == host and channel_widget.port == port:
                channel_widget.on_user_renamed(old_user, new_user)
