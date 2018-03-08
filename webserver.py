import socket
from io import StringIO
import sys
import re
import os

import gevent
from gevent import monkey

monkey.patch_all()

STATIC_ROOT = './static'


class WSGIServer(object):
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 128

    def __init__(self, server_address):
        # Create a listening socket
        self.listen_socket = listen_socket = socket.socket(
            self.address_family,
            self.socket_type
        )
        # Allow to reuse the same address
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind
        listen_socket.bind(server_address)
        # Activate
        listen_socket.listen(self.request_queue_size)
        # Get server host name and port
        host, port = self.listen_socket.getsockname()[:2]
        # self.server_name = host
        self.server_name = socket.getfqdn(host)
        self.server_port = port
        # Return headers set by Web framework/Web application
        self.headers_set = []

    def set_app(self, application):
        self.application = application

    def serve_forever(self):
        listen_socket = self.listen_socket
        while True:
            # New client connection
            client_connection, client_address = listen_socket.accept()
            # Handle one request and close the client connection. Then
            # loop over to wait for another client connection
            gevent.spawn(self.handle_one_request, client_connection, client_address)
            # self.handle_one_request()

    def handle_one_request(self, client_connection, client_address):
        self.request_data = request_data = client_connection.recv(2048)
        print('接收到来自', client_address, '的请求')
        # Print formatted request data a la 'curl -v'
        request_line = request_data.decode().splitlines()[0]
        print(request_line)

        self.parse_request(request_data)
        # 判断是否为静态文件
        if re.match(r'^/static', self.path):
            self.process_static(client_connection)
            return

            # Construct environment dictionary using request data
        env = self.get_environ()

        # It's time to call our application callable and get
        # back a result that will become HTTP response body

        result = self.application(env, self.start_response)

        # Construct a response and send it back to the client
        self.finish_response(result, client_connection)

    def process_static(self, client_connection):
        # 处理静态文件
        path_info = re.match(r'^/static/(.*)', self.path).group(1)
        file_name = os.path.join(STATIC_ROOT, path_info)
        if os.path.isfile(file_name):
            with open(file_name, 'rb') as f:
                file_data = f.read()
            # print(content)
            # 文件存在，给客户端回HTTP响应报文
            # 响应行
            response_line = "HTTP/1.1 200 OK\r\n"
            # 响应头
            response_headers = "Server: PWS\r\n"
            if path_info.endswith('.html'):
                # 保证中文显示
                response_headers = response_headers + "Content-Type: text/html;charset=utf-8\r\n"
            # 响应体
            response_body = file_data
            # 拼接响应报文  发送给客户端
            response_data = (response_line + response_headers + '\r\n').encode() + response_body
            # send函数的返回值代表 成功发送的字节数----> 可能一下不能全部发送完数据
            # client_socket.send(response_data)
            client_connection.sendall(response_data)
            client_connection.close()
            return

            # 用户请求的资源路径不存在 应该返回404 Not Found
            # 响应行

        response_line = "HTTP/1.1 404 Not Found\r\n"
        # 响应头
        response_headers = "Server: PWS\r\n"
        # 响应体
        response_body = """
                <!DOCTYPE html>
                <html lang="zh">
                <head>
                    <meta charset="UTF-8">
                    <title>页面不存在</title>
                </head>
                <body>
                    <div style="background:red; height:90px; border: 1px red solid;">
                    <h1 style="text-align: center;margin:30 auto;">页面不存在</h1>
                    <div>
                </body>
                </html>
                """
        response_data = response_line + response_headers + "\r\n" + response_body
        # send函数的返回值代表 成功发送的字节数----> 可能一下不能全部发送完数据
        client_connection.sendall(response_data.encode())
        client_connection.close()
        return
        # 请求本地文件

    def parse_request(self, text):
        request_line = text.decode().splitlines()[0]
        request_line = request_line.rstrip('\r\n')
        # Break down the request line into components
        (self.request_method,  # GET
         self.path,  # /hello
         self.request_version  # HTTP/1.1
         ) = request_line.split()

        # self.path = self.path.lstrip('/')

    def get_environ(self):
        env = {}
        # The following code snippet does not follow PEP8 conventions
        # but it's formatted the way it is for demonstration purposes
        # to emphasize the required variables and their values
        #
        # Required WSGI variables
        env['wsgi.version'] = (1, 1)
        env['wsgi.url_scheme'] = 'http'
        env['wsgi.input'] = StringIO(self.request_data.decode())
        env['wsgi.errors'] = sys.stderr
        env['wsgi.multithread'] = False
        env['wsgi.multiprocess'] = False
        env['wsgi.run_once'] = False
        # Required CGI variables
        env['REQUEST_METHOD'] = self.request_method  # GET
        env['PATH_INFO'] = self.path  # /hello
        env['SERVER_NAME'] = self.server_name  # localhost
        env['SERVER_PORT'] = str(self.server_port)  # 8888

        return env

    def start_response(self, status, response_headers, exc_info=None):
        # Add necessary server headers
        server_headers = [
            ('Date', 'Tue, 31 Mar 2015 12:54:48 GMT'),
            ('Server', 'WSGIServer 0.2'),
        ]
        self.headers_set = [status, response_headers + server_headers]
        print("响应状态：", status)

        # To adhere to WSGI specification the start_response must return
        # a 'write' callable. We simplicity's sake we'll ignore that detail
        # for now.
        # return self.finish_response

    def finish_response(self, result, client_connection):
        try:
            status, response_headers = self.headers_set
            response = 'HTTP/1.1 {status}\r\n'.format(status=status)
            for header in response_headers:
                response += '{0}: {1}\r\n'.format(*header)
            response += '\r\n'
            response = response.encode()
            for data in result:
                response += data
            # response.encode()
            # Print formatted response data a la 'curl -v'
            # response = response.decode()
            # print(''.join(
            #     '> {line}\n'.format(line=line)
            #     for line in response.splitlines()
            # ))
            client_connection.sendall(response)
        finally:
            client_connection.close()


SERVER_ADDRESS = (HOST, PORT) = 'localhost', 8000


def make_server(server_address, application):
    server = WSGIServer(server_address)
    server.set_app(application)
    return server


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Provide a WSGI application object as module:callable')
    app_path = sys.argv[1]
    module, application = app_path.split(':')
    module = __import__(module)
    application = getattr(module, application)
    httpd = make_server(SERVER_ADDRESS, application)
    print('WSGIServer: Serving HTTP on port {port} ...\n'.format(port=PORT))
    httpd.serve_forever()
