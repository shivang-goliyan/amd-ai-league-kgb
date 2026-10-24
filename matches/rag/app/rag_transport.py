"""Local transport for a model/index process retained across grader exec calls."""
import json
import socket
import socketserver
from pathlib import Path
MAX_MESSAGE=65536


def request(socket_path,payload,timeout):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
        connection.settimeout(timeout);connection.connect(str(socket_path));connection.sendall(json.dumps(payload).encode()+b'\n')
        with connection.makefile('rb') as stream:line=stream.readline(MAX_MESSAGE)
    if not line.endswith(b'\n'):raise ValueError('Incomplete RAG response')
    return json.loads(line)


def make_server(socket_path,handle):
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            try:
                data=self.rfile.readline(MAX_MESSAGE)
                if not data.endswith(b'\n'):raise ValueError('Incomplete RAG request')
                result=handle(json.loads(data))
            except Exception as exc:result={'answer':'','citations':[],'confidence':0.0,'error':str(exc)}
            try:self.wfile.write(json.dumps(result,ensure_ascii=False).encode()+b'\n')
            except (BrokenPipeError,ConnectionResetError):pass
    path=Path(socket_path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():path.unlink()
    return socketserver.UnixStreamServer(str(path),Handler)
