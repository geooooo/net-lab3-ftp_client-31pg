"""
    FTP-клиент
"""


from socket import socket


class FTPClientError(Exception):
    pass


class FTPClient:

    DATA_LEN = 64000
    TIMEOUT = 5

    def __init__(self, host="localhost", port=21):
        self._is_authorize = False
        self.socket_control = socket()
        self.socket_control.settimeout(self.TIMEOUT)
        self.socket_control.connect((host, port))
        self._is_ok_status(220, "Ошибка при соединении с сервером !")

    def __del__(self):
        self._close()

    def _is_ok_status(self, ok_status, error_message):
        cur_status, _ = self._parse_response(self._read())
        if cur_status != ok_status:
            self._trigger_error(error_message)

    def _trigger_error(self, message):
        self.socket_control.close()
        raise FTPClientError(message)

    def _port_encode(port):
        byte_high = (port & 0xff00) >> 8
        byte_low = port & 0x00ff
        return (byte_high, byte_low)

    def _write(self, data):
        self.socket_control.send("{0}\n".format(data).encode("utf-8"))

    def _read(self):
        return self.socket_control.recv(self.DATA_LEN)

    def _parse_response(self, response):
        status, title = response.split(" ", 2)
        return int(status), title

    def _check_connection(self, data):
        pass

    def _close(self):
        self._write("QUIT")
        self.socket_control.close()

    def authorize(self, login, pwd):
        self._write("USER {0}".format(login))
        self._is_ok_status(331, "Ошибка при авторизации !")
        self._write("PASS {0}".format(pwd))
        self._is_ok_status(230, "Ошибка при авторизации !")
        self._is_authorize = True

    def cd(self, path):
        pass

    def mkdir(self, dir_name):
        pass

    def delete_dir(self, dir_name):
        pass

    def delete_file(self, file_name):
        pass

    def rename(self, old_name, new_name):
        pass

    def list(self, dir_name):
        pass
