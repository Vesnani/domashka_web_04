
import json
import mimetypes
import socket
import urllib.parse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import pathlib
from threading import Thread


BASE_DIR = pathlib.Path()
HTTP_IP = '0.0.0.0'
HTTP_PORT = 3000
SOCKET_IP = '127.0.0.1'
SOCKET_PORT = 5000
STORAGE_DIR = pathlib.Path('storage')
FILE_STORAGE = STORAGE_DIR / 'data.json'


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html('index.html')
            case '/message.html':
                self.send_html('message.html')
            case _:
                if pathlib.Path(route.path[:1]).exists():
                    self.send_static(route.path)
                else:
                    self.send_html('error.html', 404)

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        send_data_to_socker(body)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_static(self, path):
        self.send_response(200)
        mt = mimetypes.guess_type(path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{path}', 'rb') as file:
            self.wfile.write(file.read())


def send_data_to_socker(data):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(data, (SOCKET_IP, SOCKET_PORT))
    client_socket.close()


def run_http_server(server=HTTPServer, handler=HttpHandler):
    address = (HTTP_IP, HTTP_PORT)
    http_server = server(address, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


def run_socket_server(ip=SOCKET_IP, port=SOCKET_PORT):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind(server)
    try:
        while True:
            data, address = server_socket.recvfrom(1024)
            save_data_to_json(data)
    except KeyboardInterrupt:
        server_socket.close()


def save_data_to_json(data):
    data_parse = urllib.parse.unquote_plus(data.decode())
    data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
    try:
        with open(FILE_STORAGE, 'r', encoding='utf-8') as f:
            storage = json.load(f)
    except ValueError:
        storage = {}

    current_time = str(datetime.now())
    storage.update({current_time: data_dict})

    with open(FILE_STORAGE, 'w', encoding='utf-8') as f:
        json.dump(storage, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    STORAGE_DIR = pathlib.Path().joinpath('storage')
    FILE_STORAGE = STORAGE_DIR / 'data.json'
    if not FILE_STORAGE.exists():
        with open(FILE_STORAGE, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False)

    http_server = Thread(target=run_http_server)
    socket_sever = Thread(target=run_socket_server)
    http_server.start()
    socket_sever.start()
