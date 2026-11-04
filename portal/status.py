"""Bounded Java Server List Ping; called by the worker, never public requests."""
import json
import socket
import struct
import time

MAX_PACKET = 65536

def varint(value):
    out = bytearray()
    for _ in range(5):
        part = value & 127
        value >>= 7
        out.append(part | (128 if value else 0))
        if not value:
            return bytes(out)
    raise ValueError("VarInt too large")

def read_exact(conn, count, deadline):
    if not 0 <= count <= MAX_PACKET:
        raise ValueError("Packet too large")
    out = bytearray()
    while len(out) < count:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Status deadline")
        conn.settimeout(remaining)
        chunk = conn.recv(count - len(out))
        if not chunk:
            raise ValueError("Truncated packet")
        out.extend(chunk)
    return bytes(out)

def read_varint(conn, deadline):
    result = 0
    for n in range(5):
        b = read_exact(conn, 1, deadline)[0]
        result |= (b & 127) << (7*n)
        if not b & 128:
            return result
    raise ValueError("Invalid VarInt")

def query(host, port):
    encoded = host.encode("utf-8")
    handshake = b"\x00" + varint(767) + varint(len(encoded)) + encoded + struct.pack(">H", port) + b"\x01"
    deadline = time.monotonic() + 3
    with socket.create_connection((host, port), timeout=2) as conn:
        conn.settimeout(2)
        conn.sendall(varint(len(handshake)) + handshake + b"\x01\x00")
        length = read_varint(conn, deadline)
        # Wrap the bounded packet in a socket-like buffer for parsing.
        from io import BytesIO
        packet = BytesIO(read_exact(conn, length, deadline))
    class Reader:
        def recv(self, count): return packet.read(count)
        def settimeout(self, timeout): pass
    reader = Reader()
    if read_varint(reader, deadline) != 0:
        raise ValueError("Unexpected packet")
    payload_length = read_varint(reader, deadline)
    payload = json.loads(read_exact(reader, payload_length, deadline).decode("utf-8"))
    players = payload.get("players") or {}
    version = payload.get("version") or {}
    online, maximum = players.get("online", 0), players.get("max", 0)
    if type(online) is not int or type(maximum) is not int or not 0 <= online <= 1000000 or not 0 <= maximum <= 1000000:
        raise ValueError("Invalid player counts")
    return online, maximum, str(version.get("name", ""))[:160]
