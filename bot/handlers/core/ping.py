"""Tiny nested handler to keep the handler layer testable and discoverable."""


def handle_ping() -> str:
    return "pong"
