# sync_timer.py

import time
import bpy

from .state import control_state, reset_runtime_state
from . import osc_server
from . import transport_sync
from . import overlay


_TIMER_REGISTERED = False
_TIMER_NAMESPACE_KEY = "_REABL_SYNC_TIMER_CALLBACK"
_HARD_RESYNC_COOLDOWN_SEC = 0.20
_PUSH_STOP_COOLDOWN_SEC = 0.50
_PUSH_PLAY_DETECT_TICKS = 3
_PUSH_RETRY_SEC = 1.50


def _now():
    return time.perf_counter()


def _request_overlay_redraw():
    overlay.tag_redraw_areas()


def _get_props():
    scene = bpy.context.scene
    if scene is None:
        return None
    return scene.reabl


def _set_status(status):
    control_state["sync_status"] = status


def _zero_desync():
    control_state["desync_sec"] = 0.0
    control_state["desync_frames"] = 0.0


def _get_playback_mode(props):
    mode = getattr(props, "playback_mode", "BLENDER")
    if mode not in {"BLENDER", "PUSH"}:
        return "BLENDER"
    return mode


def _reset_push_guard_state():
    control_state["push_guard_state"] = "NORMAL"
    control_state["push_last_stop_attempt_perf"] = 0.0
    control_state["push_stop_attempt_count"] = 0
    control_state["push_playing_detect_count"] = 0


def _apply_transport_state(desired_state):
    if desired_state not in {"PLAYING", "STOPPED"}:
        desired_state = "STOPPED"

    actual_state = "PLAYING" if transport_sync.is_animation_playing() else "STOPPED"
    applied_state = control_state.get("applied_transport_state", "UNKNOWN")

    if desired_state == applied_state and desired_state == actual_state:
        return False

    changed = False

    if desired_state == "PLAYING":
        if actual_state != "PLAYING":
            changed = transport_sync.ensure_playing()
        actual_state = "PLAYING" if transport_sync.is_animation_playing() else "STOPPED"
    else:
        if actual_state != "STOPPED":
            changed = transport_sync.ensure_stopped()
        actual_state = "PLAYING" if transport_sync.is_animation_playing() else "STOPPED"

    control_state["applied_transport_state"] = actual_state
    return changed


def _sync_playback_mode_transition(scene, props):
    mode = _get_playback_mode(props)
    previous_mode = control_state.get("active_playback_mode", "BLENDER")

    if previous_mode == mode:
        return mode

    control_state["active_playback_mode"] = mode
    control_state["applied_transport_state"] = "UNKNOWN"

    if mode == "PUSH":
        if transport_sync.is_animation_playing():
            control_state["push_guard_state"] = "CONFLICT_DETECTED"
            control_state["push_playing_detect_count"] = _PUSH_PLAY_DETECT_TICKS
        else:
            _reset_push_guard_state()
    else:
        _reset_push_guard_state()

    return mode


def _update_push_guard():
    state = control_state.get("push_guard_state", "NORMAL")
    now_perf = _now()
    is_playing = transport_sync.is_animation_playing()

    # Normal PUSH case: Blender is not playing, so follow is allowed.
    if not is_playing:
        if state in {"CONFLICT_DETECTED", "STOP_REQUESTED"}:
            control_state["push_guard_state"] = "RECOVERED"

        control_state["push_playing_detect_count"] = 0
        control_state["applied_transport_state"] = "STOPPED"
        return True

    # Blender IS playing locally. Confirm it for a few ticks first.
    detect_count = int(control_state.get("push_playing_detect_count", 0))

    if state == "NORMAL":
        detect_count += 1
        control_state["push_playing_detect_count"] = detect_count

        if detect_count >= _PUSH_PLAY_DETECT_TICKS:
            control_state["push_guard_state"] = "CONFLICT_DETECTED"

        return False

    if state == "CONFLICT_DETECTED":
        last_attempt = control_state.get("push_last_stop_attempt_perf", 0.0)

        if (now_perf - last_attempt) >= _PUSH_STOP_COOLDOWN_SEC:
            if transport_sync.ensure_stopped():
                control_state["applied_transport_state"] = "STOPPED"

            control_state["push_last_stop_attempt_perf"] = now_perf
            control_state["push_stop_attempt_count"] = int(control_state.get("push_stop_attempt_count", 0)) + 1
            control_state["push_guard_state"] = "STOP_REQUESTED"

        return False

    if state == "STOP_REQUESTED":
        if not transport_sync.is_animation_playing():
            control_state["push_guard_state"] = "RECOVERED"
            control_state["applied_transport_state"] = "STOPPED"
            return False

        last_attempt = control_state.get("push_last_stop_attempt_perf", 0.0)

        # Do not hammer stop. Wait longer before another try.
        if (now_perf - last_attempt) >= _PUSH_RETRY_SEC:
            control_state["push_guard_state"] = "CONFLICT_DETECTED"

        return False

    if state == "RECOVERED":
        control_state["push_guard_state"] = "NORMAL"
        control_state["push_playing_detect_count"] = 0
        control_state["applied_transport_state"] = "STOPPED"
        return True

    _reset_push_guard_state()
    return not transport_sync.is_animation_playing()


def _finalize_push_recovered():
    if control_state.get("push_guard_state") == "RECOVERED":
        control_state["push_guard_state"] = "NORMAL"
        control_state["push_stop_attempt_count"] = 0
        control_state["push_playing_detect_count"] = 0


def _has_fresh_remote_time(props):
    last_recv = float(control_state.get("last_time_recv_perf", 0.0) or 0.0)
    if last_recv <= 0.0:
        return False

    timeout_sec = float(props.signal_timeout)
    return (_now() - last_recv) <= timeout_sec


def _handle_stopped_or_paused(scene, props):
    remote_time = control_state["remote_time"]
    target_frame = transport_sync.time_to_frame(remote_time, scene)

    moved = transport_sync.set_frame_if_needed(target_frame, scene)
    _apply_transport_state("STOPPED")

    _zero_desync()

    if control_state["last_time_recv_perf"] > 0.0:
        _set_status("SYNCED" if not moved else "RESYNC")
    else:
        _set_status("NO_SIGNAL")


def _handle_playing(scene, props):
    last_recv = control_state["last_time_recv_perf"]
    if last_recv <= 0.0:
        _zero_desync()
        _set_status("NO_SIGNAL")
        return

    timeout_sec = float(props.signal_timeout)
    since_last_time = _now() - last_recv
    if since_last_time > timeout_sec:
        _zero_desync()
        _set_status("NO_SIGNAL")
        return

    remote_time = control_state["remote_time"]
    elapsed_local = _now() - last_recv
    expected_remote_now = remote_time + elapsed_local

    target_frame = transport_sync.time_to_frame(expected_remote_now, scene)

    if not transport_sync.is_frame_in_animation_range(target_frame, scene):
        _zero_desync()
        _set_status("OUT_OF_RANGE")
        return

    _apply_transport_state("PLAYING")

    local_time = transport_sync.get_local_time_seconds(scene)

    error_sec = expected_remote_now - local_time
    fps = transport_sync.get_scene_fps(scene)
    error_frames = error_sec * fps

    control_state["desync_sec"] = error_sec
    control_state["desync_frames"] = error_frames

    hard = float(props.hard_desync_frames)
    soft = float(props.soft_desync_frames)
    now_perf = _now()
    last_resync = control_state.get("last_hard_resync_perf", 0.0)

    if abs(error_frames) >= hard:
        if (now_perf - last_resync) >= _HARD_RESYNC_COOLDOWN_SEC:
            transport_sync.hard_resync_to_frame(target_frame, scene)
            control_state["last_seek_target"] = expected_remote_now
            control_state["last_hard_resync_perf"] = now_perf
            control_state["applied_transport_state"] = "PLAYING" if transport_sync.is_animation_playing() else "STOPPED"
            _set_status("RESYNC")
        else:
            _set_status("DRIFT")
    elif abs(error_frames) >= soft:
        _set_status("DRIFT")
    else:
        _set_status("SYNCED")


def _handle_blender_idle_follow(scene, props):
    if transport_sync.is_animation_playing():
        _zero_desync()
        _set_status("NO_SIGNAL")
        return

    if not _has_fresh_remote_time(props):
        _zero_desync()
        _set_status("NO_SIGNAL")
        return

    remote_time = control_state["remote_time"]
    target_frame = transport_sync.time_to_frame(remote_time, scene)

    if not transport_sync.is_frame_in_animation_range(target_frame, scene):
        _zero_desync()
        _set_status("OUT_OF_RANGE")
        return

    moved = transport_sync.set_frame_if_needed(target_frame, scene)
    _zero_desync()
    _set_status("SYNCED" if not moved else "RESYNC")


def _handle_push_follow(scene, props):
    guard_ready = _update_push_guard()
    if not guard_ready:
        _zero_desync()
        if transport_sync.is_animation_playing():
            _set_status("DRIFT")
        return

    last_recv = control_state["last_time_recv_perf"]
    if last_recv <= 0.0:
        _zero_desync()
        _finalize_push_recovered()
        _set_status("NO_SIGNAL")
        return

    timeout_sec = float(props.signal_timeout)
    since_last_time = _now() - last_recv
    if since_last_time > timeout_sec:
        _zero_desync()
        _finalize_push_recovered()
        _set_status("NO_SIGNAL")
        return

    remote_time = control_state["remote_time"]
    target_frame = transport_sync.time_to_frame(remote_time, scene)

    if not transport_sync.is_frame_in_animation_range(target_frame, scene):
        _zero_desync()
        _finalize_push_recovered()
        _set_status("OUT_OF_RANGE")
        return

    transport_sync.set_frame_if_needed(target_frame, scene)
    control_state["applied_transport_state"] = "STOPPED"
    _zero_desync()
    _finalize_push_recovered()
    _set_status("SYNCED")


def _handle_push_idle(scene, props):
    guard_ready = _update_push_guard()
    if not guard_ready:
        _zero_desync()
        if transport_sync.is_animation_playing():
            _set_status("DRIFT")
        return

    control_state["applied_transport_state"] = "STOPPED"
    _zero_desync()
    _finalize_push_recovered()
    _set_status("NO_SIGNAL")


def _ensure_server_state(props):
    want_enabled = bool(props.sync_enabled)
    port = int(props.osc_port)

    if want_enabled:
        if not osc_server.is_server_running():
            ok, msg = osc_server.start_osc_server(port)
            control_state["osc_running"] = bool(ok)
            control_state["last_error"] = "" if ok else str(msg)
        else:
            control_state["osc_running"] = True
            control_state["last_error"] = ""
    else:
        if osc_server.is_server_running():
            osc_server.stop_osc_server()
        control_state["osc_running"] = False
        control_state["last_error"] = ""
        control_state["applied_transport_state"] = "UNKNOWN"
        _set_status("NO_SIGNAL")


def sync_timer_callback():
    scene = bpy.context.scene
    if scene is None:
        _request_overlay_redraw()
        return 0.1

    props = _get_props()
    if props is None:
        _request_overlay_redraw()
        return 0.1

    if not osc_server.dependencies_ok():
        if osc_server.is_server_running():
            osc_server.stop_osc_server()

        control_state["osc_running"] = False
        control_state["sync_enabled"] = False
        control_state["applied_transport_state"] = "UNKNOWN"
        control_state["last_error"] = osc_server.get_dependency_error_message()
        _set_status("NO_SIGNAL")
        _request_overlay_redraw()
        return 0.1

    if not props.sync_enabled:
        if osc_server.is_server_running():
            osc_server.stop_osc_server()

        if control_state["sync_enabled"] or control_state["osc_running"]:
            reset_runtime_state()
            control_state["sync_enabled"] = False

        _request_overlay_redraw()
        return 0.1

    control_state["sync_enabled"] = True

    _ensure_server_state(props)

    playback_mode = _sync_playback_mode_transition(scene, props)
    remote_transport = control_state["remote_transport"]

    if playback_mode == "PUSH":
        if remote_transport in {"playing", "paused", "stopped"}:
            _handle_push_follow(scene, props)
        else:
            _handle_push_idle(scene, props)
    else:
        if remote_transport in {"stopped", "paused"}:
            _handle_stopped_or_paused(scene, props)
        elif remote_transport == "playing":
            _handle_playing(scene, props)
        else:
            _handle_blender_idle_follow(scene, props)

    _request_overlay_redraw()
    return 0.05


def register_sync_timer():
    global _TIMER_REGISTERED

    old_cb = bpy.app.driver_namespace.get(_TIMER_NAMESPACE_KEY)
    if old_cb is not None:
        try:
            bpy.app.timers.unregister(old_cb)
        except Exception:
            pass

    try:
        bpy.app.timers.unregister(sync_timer_callback)
    except Exception:
        pass

    bpy.app.timers.register(sync_timer_callback, persistent=True)
    bpy.app.driver_namespace[_TIMER_NAMESPACE_KEY] = sync_timer_callback
    _TIMER_REGISTERED = True


def unregister_sync_timer():
    global _TIMER_REGISTERED

    old_cb = bpy.app.driver_namespace.pop(_TIMER_NAMESPACE_KEY, None)
    if old_cb is not None:
        try:
            bpy.app.timers.unregister(old_cb)
        except Exception:
            pass

    try:
        bpy.app.timers.unregister(sync_timer_callback)
    except Exception:
        pass

    _TIMER_REGISTERED = False


def register():
    register_sync_timer()


def unregister():
    unregister_sync_timer()