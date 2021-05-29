# -*- coding: utf-8 -*-
from . import versions  # noqa nosort
from twisted.words.protocols import irc  # noqa nosort
from twisted.internet import reactor  # noqa nosort
from twisted.internet import protocol  # noqa nosort


signals = {}
clients = {}


class IRCClient(irc.IRCClient):
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
        self.join("##butter-test")
        # self.join("#powder")

    def joined(self, channel):
        host = self.factory.host
        port = self.factory.port
        _call_handler("channel_joined", channel=channel, host=host, port=port)

    def privmsg(self, user, channel, message):
        _call_handler(
            "message_received",
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
