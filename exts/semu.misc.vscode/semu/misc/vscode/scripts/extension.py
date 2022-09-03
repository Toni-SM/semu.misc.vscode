import __future__

import sys
import json
import time
import types
import socket
import asyncio
import threading
import traceback
import contextlib
import subprocess
from io import StringIO
from dis import COMPILER_FLAG_NAMES
try:
    from ast import PyCF_ALLOW_TOP_LEVEL_AWAIT
except ImportError:
    PyCF_ALLOW_TOP_LEVEL_AWAIT = 0

import carb
import omni.ext


_udp_server = None
_udp_clients = []

def _log_info(msg):
    # carb logging
    file, lno, func, mod = carb._get_caller_info()
    carb.log(mod, carb.logging.LEVEL_INFO, file, func, lno, msg)
    # send the message to all connected clients
    if _udp_server is not None:
        for client in _udp_clients:
            _udp_server.sendto(f"[Info][{mod}] {msg}".encode(), client)

def _log_warn(msg):
    # carb logging
    file, lno, func, mod = carb._get_caller_info()
    carb.log(mod, carb.logging.LEVEL_WARN, file, func, lno, msg)
    # send the message to all connected clients
    if _udp_server is not None:
        for client in _udp_clients:
            _udp_server.sendto(f"[Warning][{mod}] {msg}".encode(), client)

def _log_error(msg):
    # carb logging
    file, lno, func, mod = carb._get_caller_info()
    carb.log(mod, carb.logging.LEVEL_ERROR, file, func, lno, msg)
    # send the message to all connected clients
    if _udp_server is not None:
        for client in _udp_clients:
            _udp_server.sendto(f"[Error][{mod}] {msg}".encode(), client)

def _get_coroutine_flag() -> int:
    """Get the coroutine flag for the current Python version
    """
    for k, v in COMPILER_FLAG_NAMES.items():
        if v == "COROUTINE":
            return k
    return -1

COROUTINE_FLAG = _get_coroutine_flag()

def _has_coroutine_flag(code) -> bool:
    """Check if the code has the coroutine flag set
    """
    if COROUTINE_FLAG == -1:
        return False
    return bool(code.co_flags & COROUTINE_FLAG)

def _get_compiler_flags() -> int:
    """Get the compiler flags for the current Python version
    """
    flags = 0
    for value in globals().values():
        try:
            if isinstance(value, __future__._Feature):
                f = value.compiler_flag
                flags |= f
        except BaseException:
            pass
    flags = flags | PyCF_ALLOW_TOP_LEVEL_AWAIT
    return flags

def _get_event_loop() -> asyncio.AbstractEventLoop:
    """Backward compatible function for getting the event loop
    """
    try:
        if sys.version_info >= (3, 7):
            return asyncio.get_running_loop()
        else:
            return asyncio.get_event_loop()
    except RuntimeError:
        return asyncio.get_event_loop_policy().get_event_loop()


class Extension(omni.ext.IExt):
    
    WINDOW_NAME = "Embedded VS Code"
    MENU_PATH = f"Window/{WINDOW_NAME}"

    def on_startup(self, ext_id):

        self._globals = {**globals()}
        self._locals = self._globals

        # get extension settings
        self._settings = carb.settings.get_settings()
        self._socket_ip = self._settings.get("/exts/semu.misc.vscode/socket_ip")
        self._socket_port = self._settings.get("/exts/semu.misc.vscode/socket_port")
        self._carb_logging = self._settings.get("/exts/semu.misc.vscode/carb_logging")
        kill_processes_with_port_in_use = self._settings.get("/exts/semu.misc.vscode/kill_processes_with_port_in_use")

        # menu item
        self._editor_menu = omni.kit.ui.get_editor_menu()
        if self._editor_menu:
            self._menu = self._editor_menu.add_item(Extension.MENU_PATH, self._show_notification, toggle=False, value=False)
        
        # shutdown stream
        self.shutdown_stream_ebent = omni.kit.app.get_app().get_shutdown_event_stream() \
            .create_subscription_to_pop(self._on_shutdown_event, name="semu.misc.vscode", order=0)

        # ensure port is free
        if kill_processes_with_port_in_use:
            if sys.platform == "win32":
                pids = []
                cmd = ["netstat", "-ano"]
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
                for line in p.stdout:
                    if str(self._socket_port).encode() in line:
                        pids.append(line.strip().split(b" ")[-1].decode())
                p.wait()
                for pid in pids:
                    carb.log_warn(f"Forced process shutdown with PID {pid}")
                    cmd = ["taskkill", "/PID", pid, "/F"]
                    subprocess.Popen(cmd).wait()

        # create socket
        self._socket_last_error = ""
        self._server = None
        self._create_socket()

        # carb logging to VS Code
        if self._carb_logging:
            # create UDP socket
            self._udp_server_running = False
            threading.Thread(target=self._create_udp_socket).start()

            # checkpoint carb log functions
            self._carb_log_info = types.FunctionType(carb.log_info.__code__, 
                                                     carb.log_info.__globals__, 
                                                     carb.log_info.__name__, 
                                                     carb.log_info.__defaults__, 
                                                     carb.log_info.__closure__)
            self._carb_log_warn = types.FunctionType(carb.log_warn.__code__,
                                                     carb.log_warn.__globals__,
                                                     carb.log_warn.__name__,
                                                     carb.log_warn.__defaults__,
                                                     carb.log_warn.__closure__)
            self._carb_log_error = types.FunctionType(carb.log_error.__code__,
                                                     carb.log_error.__globals__,
                                                     carb.log_error.__name__,
                                                     carb.log_error.__defaults__,
                                                     carb.log_error.__closure__)
        
            # override carb log functions
            carb.log_info = types.FunctionType(_log_info.__code__, 
                                               _log_info.__globals__, 
                                               _log_info.__name__, 
                                               _log_info.__defaults__, 
                                               _log_info.__closure__)
            carb.log_warn = types.FunctionType(_log_warn.__code__,
                                               _log_warn.__globals__,
                                               _log_warn.__name__,
                                               _log_warn.__defaults__,
                                               _log_warn.__closure__)
            carb.log_error = types.FunctionType(_log_error.__code__,
                                                _log_error.__globals__,
                                                _log_error.__name__,
                                                _log_error.__defaults__,
                                                _log_error.__closure__)
        
    def on_shutdown(self):
        global _udp_server, _udp_clients
        # restore carb log functions
        if self._carb_logging:
            carb.log_info = self._carb_log_info
            carb.log_warn = self._carb_log_warn
            carb.log_error = self._carb_log_error
        # clean up menu item
        if self._menu is not None:
            try:
                self._editor_menu.remove_item(self._menu)
            except:
                self._editor_menu.remove_item(Extension.MENU_PATH)
            self._menu = None
        # close the socket
        if self._server:
            self._server.close()
            _get_event_loop().run_until_complete(self._server.wait_closed())
        # close the UDP socket
        if self._carb_logging:
            _udp_server = None
            _udp_clients = []
            # wait for the UDP socket to close
            while self._udp_server_running:
                time.sleep(0.1)

    # extension ui methods

    def _on_shutdown_event(self, event):
        if event.type == omni.kit.app.POST_QUIT_EVENT_TYPE:
            self.on_shutdown()

    def _show_notification(self, *args, **kwargs) -> None:
        """Show extension data in the notification area
        """
        if self._server is None:
            notification = "Unable to start the socket server at {}:{}. {}".format(self._socket_ip, self._socket_port, self._socket_last_error)
            status=omni.kit.notification_manager.NotificationStatus.WARNING
        else:
            notification = "Embedded VS Code socket server is running at {}:{}.\nUDP socket server for carb logging is {}"\
                .format(self._socket_ip, self._socket_port, "enabled" if self._carb_logging else "disabled")
            status=omni.kit.notification_manager.NotificationStatus.INFO

        ok_button = omni.kit.notification_manager.NotificationButtonInfo("OK", on_complete=None)
        omni.kit.notification_manager.post_notification(notification, 
                                                        hide_after_timeout=False, 
                                                        duration=0, 
                                                        status=status, 
                                                        button_infos=[ok_button])
        
        print(notification)
        carb.log_info(notification)

    # internal socket methods

    def _create_udp_socket(self) -> None:
        """Create the UDP socket for broadcasting carb logging
        """
        global _udp_server, _udp_clients

        self._udp_server_running = True
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as _server:
            try:
                _server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                _server.bind((self._socket_ip, self._socket_port))
                _server.setblocking(False)
                _server.settimeout(0.1)
            except Exception as e:
                _udp_server = None
                _udp_clients = []
                carb.log_error(str(e))
                self._udp_server_running = False
                return

            _udp_server = _server
            _udp_clients = []

            while _udp_server is not None:
                try:
                    _, addr = _server.recvfrom(1024)
                    if addr not in _udp_clients:
                        _udp_clients.append(addr)
                except socket.timeout:
                    pass
                except Exception as e:
                    carb.log_error("UDP server error: {}".format(e))
                    break
        self._udp_server_running = False

    def _create_socket(self) -> None:
        """Create a socket server to listen for incoming connections from the client
        """
        class ServerProtocol(asyncio.Protocol):
            def __init__(self, parent) -> None:
                super().__init__()
                self._parent = parent

            def connection_made(self, transport):
                peername = transport.get_extra_info('peername')
                self.transport = transport

            def data_received(self, data):
                asyncio.run_coroutine_threadsafe(self._parent._exec_code_async(data.decode(), self.transport),
                                                 _get_event_loop())

        async def server_task():
            try:
                self._server = await _get_event_loop().create_server(protocol_factory=lambda: ServerProtocol(self), 
                                                                     host=self._socket_ip, 
                                                                     port=self._socket_port,
                                                                     family=socket.AF_INET,
                                                                     reuse_port=None if sys.platform == 'win32' else True)
            except Exception as e:
                self._server = None
                self._socket_last_error = str(e)
                carb.log_error(str(e))
                return
            
            await self._server.start_serving()

        task = _get_event_loop().create_task(server_task())

    async def _exec_code_async(self, statement: str, transport: asyncio.Transport) -> None:
        """Execute the statement in the Omniverse scope and send the result to the client
        
        :param statement: statement to execute
        :type statement: str
        :param transport: transport to send the result to the client
        :type transport: asyncio.Transport

        :return: reply dictionary as expected by the client
        :rtype: dict
        """
        _stdout = StringIO()
        try:
            with contextlib.redirect_stdout(_stdout):
                should_exec_code = True
                # try 'eval' first
                try:
                    code = compile(statement, "<string>", "eval", flags= _get_compiler_flags(), dont_inherit=True)
                except SyntaxError:
                    pass
                else:
                    result = eval(code, self._globals, self._locals)
                    should_exec_code = False
                # if 'eval' fails, try 'exec'
                if should_exec_code:
                    code = compile(statement, "<string>", "exec", flags= _get_compiler_flags(), dont_inherit=True)
                    result = eval(code, self._globals, self._locals)
                # await the result if it is a coroutine
                if _has_coroutine_flag(code):
                    result = await result
        except Exception as e:
            # clean traceback
            _traceback = traceback.format_exc()
            _i = _traceback.find('\n  File "<string>"')
            if _i != -1:
                _traceback = _traceback[_i + 20:]
            _traceback = _traceback.replace(", in <module>\n", "\n")
            # build reply dictionary
            reply = {"status": "error", 
                    "traceback": [_traceback],
                    "ename": str(type(e).__name__),
                    "evalue": str(e)}
        else:
            reply = {"status": "ok"}

        # add output to reply dictionary for printing
        reply["output"] = _stdout.getvalue()
        if reply["output"].endswith('\n'):
            reply["output"] = reply["output"][:-1]

        # send the reply to the client
        reply = json.dumps(reply)
        transport.write(reply.encode())

        # close the connection
        transport.close()
