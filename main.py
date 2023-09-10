from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from datetime import datetime
import urllib.parse
import pathlib
import mimetypes
import socket
import json


UDP_IP = '127.0.0.1'
UDP_PORT = 5000
JSON_STORAGE = 'storage/data.json'


# HTTP server
class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/contact':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)
    
    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        run_client(UDP_IP, UDP_PORT, data_dict)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


# Server
def run_server(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)
    try:
        while True:
            data, address = sock.recvfrom(1024)
            ready_to_be_stored = eval(data.decode())
            print('on server:', ready_to_be_stored)
            add_to_storage(JSON_STORAGE, ready_to_be_stored)
    except KeyboardInterrupt:
        print(f'Destroy server')
    finally:
        sock.close()

# Client
def run_client(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    print("on client:", message)
    str_data = str(message)
    data = str_data.encode()
    sock.sendto(data, server)
    sock.close()


def add_to_storage(file_path, new_data):
    with open(file_path, 'r') as file:
        data = json.load(file)

    now_key = str(datetime.now())
    data[now_key] = new_data

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)



def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == '__main__':
    thread1 = Thread(target=run)
    thread2 = Thread(target=run_server, args=(UDP_IP, UDP_PORT))
    thread1.start()
    thread2.start()