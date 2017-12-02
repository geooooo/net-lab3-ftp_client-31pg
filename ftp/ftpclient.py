"""
    FTP-клиент
"""


from socket import socket


class FTPClientError(Exception):
    pass


class FTPClient:

    # public

    def cd(self, path):
        self._check_connection()
        self._cd(path)

    def mkdir(self, dir_name):
        self._check_connection()
        self._mkdir(dir_name)

    def delete_dir(self, dir_name):
        self._check_connection()
        self._delete_dir(dir_name)

    def delete_file(self, file_name):
        self._check_connection()
        self._delete_file(file_name)

    def rename(self, old_name, new_name):
        self._check_connection()
        self._rename(old_name, new_name)

    def list(self, dir_name):
        self._check_connection()
        socket_data = socket()
        socket_data.settimeout(self._TIMEOUT)
        host, port = self._get_addr_self()
        socket_data.bind((host, port))
        socket_data.listen(10)
        self._cport(host, port)
        self._list(dir_name)
        socket_server, _ = socket_data.accept()
        response = socket_server.recvmsg(self._DATA_LEN)
        socket_server.close()
        socket_data.close()
        self._is_ok_status(150, "Не удалось получить список файлов !")
        self._is_ok_status(226, "Не удалось получить список файлов !")
        return self._parse_list(response)

    def put_file(self, file_name):
        self._check_connection()
        self._pasv()
        self._is_ok_status(227, "Не удалось открыть пассивное соединение !")
        response = self._read(True)
        _, addr = response.rsplit(" ", 1)
        ip, port = self._get_addr_server(addr[1:-2])
        self._type("I")
        self._is_ok_status(200, "Не удалось отправить файл !")
        self._stor(file_name.rsplit("/")[-1])
        socket_data = socket()
        socket_data.connect((ip, port))
        file_data = open(file_name, "rb").read()
        socket_data.send(file_data)
        self._is_ok_status(150, "Не удалось отправить файл !")
        socket_data.close()

    def get_file(self, file_name):
        self._check_connection()
        self._pasv()
        self._is_ok_status(227, "Не удалось открыть пассивное соединение !")
        response = self._read(True)
        _, addr = response.rsplit(" ", 1)
        ip, port = self._get_addr_server(addr[1:-2])
        self._type("I")
        self._is_ok_status(200, "Не удалось получить файл !")
        self._retr(file_name)
        socket_data = socket()
        socket_data.connect((ip, port))
        with open(file_name.rsplit("/")[-1], "wb") as f:
            while True:
                data = socket_data.recv(self._DATA_LEN)
                if not data:
                    break
                f.write(data)
        self._is_ok_status(150, "Не удалось получить файл !")
        socket_data.close()

    # private

    _DATA_LEN = 64000
    _TIMEOUT = 60

    def __init__(self, host="localhost", port=21, login="anonymous", pwd=""):
        self._host = host
        self._port = port
        self._login = login
        self._pwd = pwd
        self._socket_control = socket()
        self._socket_control.settimeout(self._TIMEOUT)
        self._connect()

    def __del__(self):
        self._close()

    def _connect(self):
        self._socket_control.connect((self._host, self._port))
        self._is_ok_status(220, "Ошибка при соединении с сервером !")
        self._authorize()

    def _is_ok_status(self, ok_status, error_message):
        cur_status, _ = self._parse_response(self._read())
        if cur_status != ok_status:
            self._trigger_error(error_message)

    def _authorize(self):
        self._write("USER {0}".format(self._login))
        self._is_ok_status(331, "Ошибка при авторизации !")
        self._write("PASS {0}".format(self._pwd))
        self._is_ok_status(230, "Ошибка при авторизации !")

    def _trigger_error(self, message):
        self._write("ABOR")
        raise FTPClientError(message)

    def _check_connection(self):
        try:
            self._cd(".")
        except FTPClientError:
            self._connect()

    def _write(self, data):
        self._socket_control.send("{0}\n".format(data).encode("utf-8"))

    def _read(self, is_return_last=False):
        if is_return_last and hasattr(self, "_read_last_return"):
            result = self._read_last_return
        else:
            if not hasattr(self, "_buffer"):
                self._buffer = []
            if not self._buffer:
                data = self._socket_control.recv(self._DATA_LEN).decode()
                self._buffer.extend([msg for msg in data.split("\r\n") if msg])
            result = self._read_last_return = self._buffer.pop(0)
        return result

    def _parse_response(self, response):
        print(response)
        status, title = response.split(" ", 1)
        return int(status), title

    def _parse_list(self, response):
        response = response[0].decode("utf-8")
        from pprint import pprint
        lines = [line for line in response.split("\r\n") if line]
        files = []
        for line in lines:
            parts = [part for part in line.split(" ") if part]
            files.append({
                "attrs": parts[0],
                "size": parts[4],
                "datetime": "{0} {1} {2}".format(parts[5], parts[6], parts[7]),
                "name": parts[8]
            })
        pprint(files)
        return files

    def _port_encode(self, port):
        byte_high = (port & 0xff00) >> 8
        byte_low = port & 0x00ff
        return (byte_high, byte_low)

    def _port_decode(self, port_bytes):
        byte_high, byte_low = port_bytes
        return byte_high << 8 | byte_low

    def _get_addr_self(self):
        host = "127.0.0.1"
        port = 8814
        return (host, port)

    def _get_addr_server(self, addr):
        ip, byte_high, byte_low = addr.rsplit(",", 2)
        ip = ip.replace(",", ".")
        port = self._port_decode((int(byte_high), int(byte_low)))
        return ip, port

    def _close(self):
        self._write("QUIT")
        self._socket_control.close()

    def _cd(self, path):
        self._write("CWD {0}".format(path))
        self._is_ok_status(250, "Ошибка при смене директории !")

    def _mkdir(self, dir_name):
        self._write("MKD {0}".format(dir_name))
        self._is_ok_status(257, "Ошибка при создании директории !")

    def _delete_dir(self, dir_name):
        self._write("RMD {0}".format(dir_name))
        self._is_ok_status(250, "Ошибка при удалении директории !")

    def _delete_file(self, file_name):
        self._write("DELE {0}".format(file_name))
        self._is_ok_status(250, "Ошибка при удалении файла !")

    def _rename(self, old_name, new_name):
        self._write("RNFR {0}".format(old_name))
        self._is_ok_status(350, "Ошибка при переименовывании файла !")
        self._write("RNTO {0}".format(new_name))
        self._is_ok_status(250, "Ошибка при переименовывании файла !")

    def _list(self, dir_name):
        self._write("LIST {0}".format(dir_name))

    def _cport(self, host, port):
        host = host.replace(".", ",")
        port_bytes = [str(num) for num in self._port_encode(int(port))]
        port = ",".join(port_bytes)
        self._write("PORT {0},{1}".format(host, port))
        self._is_ok_status(200, "Ошибка при создании канала передачи данных !")

    def _pasv(self):
        self._write("PASV")

    def _retr(self, file_name):
        self._write("RETR {0}".format(file_name))

    def _stor(self, file_name):
        self._write("STOR {0}".format(file_name))

    def _type(self, ctype):
        self._write("TYPE {0}".format(ctype))
