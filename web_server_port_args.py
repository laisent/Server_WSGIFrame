# -*- coding: utf-8 -*-
import socket
import re
import multiprocessing
# import dynamic.mini_frame
import sys


class WSGIServer(object):
    def __init__(self, port, app, static_path):
        # 1.创建套接字
        self.tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # 2.绑定
        self.tcp_server_socket.bind(("", port))

        # 3.变为监听套接字
        self.tcp_server_socket.listen(128)

        self.application = app
        self.static_path = static_path

    def service_client(self, new_socket):
        """为这个客户端返回数据"""

        # 1.接收浏览器发送过来的请求，即http请求
        # GET / HTTP/1.1
        # ...
        request = new_socket.recv(1024).decode("utf-8")

        if len(request)>0:
            request_lines = request.splitlines()
            print(">" * 20)

            # GET / HTTP / 1.1
            # get post put del
            file_name = ""
            ret = re.match(r"[^/]+(/[^ ]*)", request_lines[0])
            if ret:
                file_name = ret.group(1)
                print("*" * 50)
                print(file_name)
                if file_name == "/":
                    file_name += "index.html"

            # 如果请求的资源不是以.py结尾，那么就认为是静态资源（html/css/js/png,jpg等）
            if not file_name.endswith(".py"):
                try:
                    f = open(self.static_path + file_name, "rb")
                except:
                    response = "HTTP/1.1 404 NOT FOUND\r\n"
                    response += "\r\n"
                    response += "-----file not found-----"
                    new_socket.send(response.encode("utf-8"))
                else:
                    html_content = f.read()
                    f.close()

                    # 2.返回http格式的数据，给浏览器
                    # 2.1 准备发送给浏览器的数据---header
                    # 2.2 准备发送给浏览器的数据---body
                    response_body = html_content

                    response_header = "HTTP/1.1 200 OK\r\n"
                    response_header += "Content-Length:%d\r\n" % len(response_body)
                    response_header += "\r\n"

                    response = response_header.encode("utf-8") + response_body

                    # 将response发送给浏览器
                    new_socket.send(response)
            else:
                # 如果是以.py结尾，那么就认为是动态资源的请求
                # response_header = "HTTP/1.1 200 OK\r\n"
                # response_header += "\r\n"
                env = dict()
                env['PATH_INFO'] = file_name
                response_body = self.application(env, self.set_response_header)

                response_header = "HTTP/1.1 %s\r\n" % self.status
                for temp in self.headers:
                    response_header += "%s:%s\r\n" % (temp[0], temp[1])
                response_header += "\r\n"

                response = response_header + response_body
                new_socket.send(response.encode("utf-8"))

        # 关闭套接字
        new_socket.close()

    def set_response_header(self, status, headers):
        self.status = status
        self.headers = [("server", "mini_web v1.0")]
        self.headers += headers

    def run_forever(self):
        """用来完成整体的控制"""
        while True:
            # 4.等待新客户端的链接
            new_socket, client_addr = self.tcp_server_socket.accept()

            # 5.为这个客户端服务
            p = multiprocessing.Process(target=self.service_client, args=(new_socket,))
            p.start()

            new_socket.close()

        # 关闭监听套接字
        self.tcp_server_socket.close()


def main():
    """控制整体 创建一个web服务器对象 然后调用这个对象的run_forever方法运行"""
    if len(sys.argv) == 3:
        try:
            port = int(sys.argv[1])
            frmae_app_name = sys.argv[2]
        except Exception as ret:
            print("端口输入格式错误！")
            return
    else:
        print("请按照以下方式运行：")
        print("python xxx.py 7890 mini_frame:application")
        return

    # mini_frame: application
    ret = re.match(r"([^:]+):(.*)", frmae_app_name)
    if ret:
        frame_name = ret.group(1)  # mini_frome
        app_name = ret.group(2)  # application
    else:
        print("请按照以下方式运行：")
        print("python xxx.py 7890 mini_frame:application")
        return

    with open("./web_server.conf") as f:
        conf_info = eval(f.read())

    sys.path.append(conf_info['dynamic_path'])
    frame = __import__(frame_name)  # 返回值标记这导入的这个模板
    app = getattr(frame, app_name)  # 此时app就指向了dynamic/mini_frame模块中的application这个函数

    wsgi_server = WSGIServer(port, app, conf_info['static_path'])
    wsgi_server.run_forever()


if __name__ == "__main__":
    main()
