"""Resident OCR request transport; inference is injected once at service startup."""
import json
import socket
import socketserver
from pathlib import Path

MAX_MESSAGE=32768

def request(socket_path, payload, timeout=24):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as conn:
        conn.settimeout(timeout);conn.connect(str(socket_path))
        conn.sendall(json.dumps(payload,ensure_ascii=False).encode()+b'\n')
        with conn.makefile('rb') as reader:
            line=reader.readline(MAX_MESSAGE)
        if not line.endswith(b'\n'):raise ValueError('Incomplete OCR response')
        return json.loads(line)


def make_server(socket_path,recognize):
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(25)
            try:
                raw=self.rfile.readline(MAX_MESSAGE)
                if not raw.endswith(b'\n'):raise ValueError('Incomplete request')
                payload=json.loads(raw);answer=recognize(payload['image'])
            except Exception as exc:
                answer={'text':'','confidence':0.0,'error':str(exc)}
            try:self.wfile.write(json.dumps(answer,ensure_ascii=False).encode()+b'\n')
            except (BrokenPipeError,ConnectionResetError):pass
    socket_path=Path(socket_path);socket_path.parent.mkdir(parents=True,exist_ok=True)
    if socket_path.exists():socket_path.unlink()
    return socketserver.UnixStreamServer(str(socket_path),Handler)
