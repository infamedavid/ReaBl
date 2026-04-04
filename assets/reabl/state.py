# state.py

control_state = {
    "sync_enabled": False,
    "osc_running": False,

    "remote_transport": "unknown",   # "playing", "paused", "stopped", "unknown"
    "remote_time": 0.0,
    "prev_remote_time": 0.0,

    "last_time_recv_perf": 0.0,
    "last_transport_recv_perf": 0.0,
    "last_hard_resync_perf": 0.0,

    "desync_sec": 0.0,
    "desync_frames": 0.0,

    "sync_status": "NO_SIGNAL",      # "NO_SIGNAL", "SYNCED", "DRIFT", "RESYNC", "OUT_OF_RANGE"
    "last_seek_target": 0.0,
    "last_error": "",

    "active_playback_mode": "BLENDER",
    "applied_transport_state": "UNKNOWN",   # "PLAYING", "STOPPED", "UNKNOWN"

    # Push guard state
    "push_guard_state": "NORMAL",    # "NORMAL", "CONFLICT_DETECTED", "STOP_REQUESTED", "RECOVERED"
    "push_last_stop_attempt_perf": 0.0,
    "push_stop_attempt_count": 0,
    "push_playing_detect_count": 0,
}


def reset_runtime_state():
    control_state["osc_running"] = False

    control_state["remote_transport"] = "unknown"
    control_state["remote_time"] = 0.0
    control_state["prev_remote_time"] = 0.0

    control_state["last_time_recv_perf"] = 0.0
    control_state["last_transport_recv_perf"] = 0.0
    control_state["last_hard_resync_perf"] = 0.0

    control_state["desync_sec"] = 0.0
    control_state["desync_frames"] = 0.0

    control_state["sync_status"] = "NO_SIGNAL"
    control_state["last_seek_target"] = 0.0
    control_state["last_error"] = ""

    control_state["active_playback_mode"] = "BLENDER"
    control_state["applied_transport_state"] = "UNKNOWN"

    control_state["push_guard_state"] = "NORMAL"
    control_state["push_last_stop_attempt_perf"] = 0.0
    control_state["push_stop_attempt_count"] = 0
    control_state["push_playing_detect_count"] = 0


def register():
    reset_runtime_state()


def unregister():
    reset_runtime_state()