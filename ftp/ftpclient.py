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
        # TODO: list

    # private

    _DATA_LEN = 64000
    _TIMEOUT = 5

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
        self._socket_control.close()
        raise FTPClientError(message)

    def _check_connection(self):
        try:
            self._cd(".")
        except FTPClientError:
            self._connect()

    def _write(self, data):
        self._socket_control.send("{0}\n".format(data).encode("utf-8"))

    def _read(self):
        return self._socket_control.recv(self._DATA_LEN)

    def _parse_response(self, response):
        status, title = response.split(" ", 2)
        return int(status), title

    def _port_encode(self, port):
        byte_high = (port & 0xff00) >> 8
        byte_low = port & 0x00ff
        return (byte_high, byte_low)

    def _close(self):
        self._write("QUIT")
        self._socket_control.close()

    def _cd(self, path):
        self._write("CWD {0}".format(path))
        self._is_ok_status(250, "Ошибка при смене директории !")

    def _mkdir(self, dir_name):
        self._write("MKD {0}".format(dir_name))
        self._is_ok_status(257, "Ошибка при создании директории !")

    def _delte_dir(self, dir_name):
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

    def _retr(self):
        pass
        # TODO: retr

    def _stor(self):
        pass
        # TODO: stor

    def _port(sefl):
        pass
        # TODO: port

    def _pasv(sefl):
        pass
        # TODO: pasv

    def _type(sefl):
        pass
        # TODO: type

    def _stru(sefl):
        pass
        # TODO: stru

    def _mode(self):
        pass
        # TODO: mode
