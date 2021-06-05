# -*- coding: utf-8 -*-
from . import versions  # noqa nosort
from twisted.words.protocols import irc  # noqa nosort
from twisted.internet import reactor  # noqa nosort
from twisted.internet import protocol  # noqa nosort


signals = {}
clients = {}


class ImprovedBaseIRCClient(irc.IRCClient):
    def names(self, channel):
        self.sendLine(f"NAMES {channel}")

    def listNames(self, channel, names):
        pass

    def irc_RPL_NAMREPLY(self, prefix, params):
        channel = params[2]
        names = params[3]
        self.listNames(channel, names.split(" "))

    def endNames(self, channel):
        pass

    def irc_RPL_ENDOFNAMES(self, prefix, params):
        channel = params[1]
        self.endNames(channel)

    def irc_unknown(self, prefix, command, params):
        print(
            "unhandled IRC command:",
            {"prefix": prefix, "command": command, "params": params},
        )

    @property
    def membership_prefixes(self):
        return [
            p[0]
            for p in sorted(
                self.supported.getFeature("PREFIX", []).values(),
                key=lambda item: item[1],
            )
        ]


class IRCClient(ImprovedBaseIRCClient):
    def __init__(self, factory):
        self.factory = factory
        self.nickname = self.factory.nickname
        server_id = f"{self.factory.host}:{self.factory.port}"
        clients[server_id] = self

    def connectionLost(self, reason):
        print("connection lost:", reason)
        server_id = f"{self.factory.host}:{self.factory.port}"
        if clients[server_id] is self:
            clients.pop(server_id)

    def signedOn(self):
        self.join("#butter-chat")
        # self.join("#powder")

    def joined(self, channel):
        host = self.factory.host
        port = self.factory.port
        _call_handler("channel_joined", channel=channel, host=host, port=port)
        _call_handler(
            "user_joined",
            user=self.nickname,
            channel=channel,
            host=self.factory.host,
            port=self.factory.port,
        )

    def listNames(self, channel, names):
        prefixes = self.membership_prefixes
        filtered_names = [name[1:] if name[0] in prefixes else name for name in names]
        _call_handler(
            "list_names",
            channel=channel,
            names=filtered_names,
            host=self.factory.host,
            port=self.factory.port,
        )

    def endNames(self, channel):
        _call_handler(
            "end_names",
            channel=channel,
            host=self.factory.host,
            port=self.factory.port,
        )

    def privmsg(self, user, channel, message):
        if channel == self.nickname:
            channel = user.split("!")[0]
        if channel == "*":
            channel = self.factory.host
        _call_handler(
            "message_received",
            user=user.split("!")[0],
            message=message,
            channel=channel,
            host=self.factory.host,
            port=self.factory.port,
        )

    def action(self, user, channel, message):
        if channel == self.nickname:
            channel = user.split("!")[0]
        if channel == "*":
            channel = self.factory.host
        _call_handler(
            "action_received",
            user=user.split("!")[0],
            message=message,
            channel=channel,
            host=self.factory.host,
            port=self.factory.port,
        )

    def noticed(self, user, channel, message):
        if channel == self.nickname:
            channel = user.split("!")[0]
        if channel == "*":
            channel = self.factory.host
        _call_handler(
            "notice_received",
            user=user.split("!")[0],
            message=message,
            channel=channel,
            host=self.factory.host,
            port=self.factory.port,
        )

    def topicUpdated(self, user, channel, newTopic):
        _call_handler(
            "topic_changed",
            topic=newTopic,
            channel=channel,
            host=self.factory.host,
            port=self.factory.port,
        )

    def userJoined(self, user, channel):
        _call_handler(
            "user_joined",
            user=user.split("!")[0],
            channel=channel,
            host=self.factory.host,
            port=self.factory.port,
        )

    def userLeft(self, user, channel):
        _call_handler(
            "user_left",
            user=user.split("!")[0],
            channel=channel,
            host=self.factory.host,
            port=self.factory.port,
        )

    # TODO: userQuit

    def userRenamed(self, oldname, newname):
        _call_handler(
            "user_renamed",
            old_user=oldname,
            new_user=newname,
            host=self.factory.host,
            port=self.factory.port,
        )

    def nickChanged(self, nick):
        _call_handler(
            "user_renamed",
            old_user=self.nickname,
            new_user=nick,
            host=self.factory.host,
            port=self.factory.port,
        )
        super().nickChanged(nick)


class IRCClientFactory(protocol.ClientFactory):
    def __init__(self, nickname, host, port):
        self.nickname = nickname
        self.host = host
        self.port = port

    def buildProtocol(self, addr):
        p = IRCClient(self)
        return p

    def clientConnectionLost(self, connector, reason):
        # TODO: exponential backoff. there's a specific factory class that does
        #       that already, so look into that.
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print("connection failed:", reason)


def register_handler(signal, f):
    if signal not in signals:
        signals[signal] = []
    signals[signal].append(f)


def _call_handler(signal, **kwargs):
    for handler in signals.get(signal, []):
        handler(**kwargs)


def connect(nickname, host, port=6667):
    f = IRCClientFactory(nickname, host, port)
    reactor.connectTCP(host, port, f)


def start():
    reactor.run()


def stop():
    reactor.stop()


def send_message(host, port, channel, message):
    server_id = f"{host}:{port}"
    client = clients.get(server_id, None)
    if client is None:
        raise ValueError(f"Not connected to {server_id}")
    client.msg(channel, message)
    _call_handler(
        "message_received",
        user=client.nickname,
        message=message,
        channel=channel,
        host=host,
        port=port,
    )


def send_action(host, port, channel, message):
    server_id = f"{host}:{port}"
    client = clients.get(server_id, None)
    if client is None:
        raise ValueError(f"Not connected to {server_id}")
    client.describe(channel, message)
    _call_handler(
        "action_received",
        user=client.nickname,
        message=message,
        channel=channel,
        host=host,
        port=port,
    )


def change_nick(nick):
    for client in clients.values():
        client.setNick(nick)


def join_channel(host, port, channel):
    server_id = f"{host}:{port}"
    client = clients.get(server_id, None)
    if client is None:
        raise ValueError(f"Not connected to {server_id}")
    client.join(channel)
