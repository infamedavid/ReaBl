# osc_server.py

import threading
import time
import importlib.util

from .state import control_state


_server = None
_server_thread = None
_SMALL_BACKWARD_JITTER_SEC = 0.20


def _now():
    return time.perf_counter()


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def has_pythonosc():
    try:
        return importlib.util.find_spec("pythonosc") is not None
    except Exception:
        return False


def get_missing_dependencies():
    missing = []
    if not has_pythonosc():
        missing.append("python-osc")
    return missing


def dependencies_ok():
    return len(get_missing_dependencies()) == 0


def get_dependency_error_message():
    if dependencies_ok():
        return ""
    return "Some dependencies missing. Check the installation manual."


def _update_transport(new_state):
    control_state["remote_transport"] = new_state
    control_state["last_transport_recv_perf"] = _now()


def _handle_play(address, *args):
    if not args:
        return

    value = _safe_int(args[0], default=0)
    if value == 1:
        _update_transport("playing")


def _handle_stop(address, *args):
    if not args:
        return

    value = _safe_int(args[0], default=0)
    if value == 1:
        _update_transport("stopped")


def _handle_pause(address, *args):
    if not args:
        return

    value = _safe_int(args[0], default=0)
    if value == 1:
        _update_transport("paused")


def _handle_time(address, *args):
    if not args:
        return

    current_time = control_state["remote_time"]
    new_time = _safe_float(args[0], default=current_time)
    delta = new_time - current_time

    if control_state["remote_transport"] == "playing":
        if delta < 0.0 and abs(delta) <= _SMALL_BACKWARD_JITTER_SEC:
            return

    control_state["prev_remote_time"] = current_time
    control_state["remote_time"] = new_time
    control_state["last_time_recv_perf"] = _now()


def _build_dispatcher():
    from pythonosc.dispatcher import Dispatcher

    dispatcher = Dispatcher()
    dispatcher.map("/reabl/transport/play", _handle_play)
    dispatcher.map("/reabl/transport/stop", _handle_stop)
    dispatcher.map("/reabl/transport/pause", _handle_pause)
    dispatcher.map("/reabl/state/time", _handle_time)
    return dispatcher


def is_server_running():
    return _server is not None and _server_thread is not None and _server_thread.is_alive()


def start_osc_server(port):
    global _server, _server_thread

    if not has_pythonosc():
        control_state["osc_running"] = False
        return False, get_dependency_error_message()

    if is_server_running():
        return True, "OSC server already running"

    try:
        from pythonosc.osc_server import BlockingOSCUDPServer

        dispatcher = _build_dispatcher()
        _server = BlockingOSCUDPServer(("0.0.0.0", int(port)), dispatcher)
    except Exception as ex:
        _server = None
        _server_thread = None
        control_state["osc_running"] = False
        return False, f"Failed to create OSC server: {ex}"

    def _serve():
        try:
            _server.serve_forever()
        except Exception:
            pass

    try:
        _server_thread = threading.Thread(target=_serve, daemon=True)
        _server_thread.start()
        control_state["osc_running"] = True
        return True, f"OSC server listening on UDP {port}"
    except Exception as ex:
        try:
            _server.server_close()
        except Exception:
            pass

        _server = None
        _server_thread = None
        control_state["osc_running"] = False
        return False, f"Failed to start OSC server thread: {ex}"


def stop_osc_server():
    global _server, _server_thread

    thread = _server_thread
    server = _server

    if server is not None:
        try:
            server.shutdown()
        except Exception:
            pass

        try:
            server.server_close()
        except Exception:
            pass

    if thread is not None:
        try:
            thread.join(timeout=0.5)
        except Exception:
            pass

    _server = None
    _server_thread = None
    control_state["osc_running"] = False


def restart_osc_server(port):
    stop_osc_server()
    return start_osc_server(port)


def register():
    pass


def unregister():
    stop_osc_server()