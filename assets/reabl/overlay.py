# overlay.py

import time

import blf
import bpy
from bpy.types import SpaceSequenceEditor, SpaceView3D

from .state import control_state
from . import transport_sync

_VIEW3D_HANDLE = None
_VSE_HANDLE = None
_POPUP_DURATION_SEC = 1.5

_previous_local_frame = None
_active_marker_popup_text = ""
_popup_expire_perf = 0.0


def _now_perf():
    return time.perf_counter()


def _get_scene_and_props(context):
    scene = getattr(context, "scene", None)
    if scene is None:
        return None, None

    props = getattr(scene, "reabl", None)
    if props is None:
        return None, None

    return scene, props


def _is_signal_fresh(props):
    last_recv = float(control_state.get("last_time_recv_perf", 0.0) or 0.0)
    if last_recv <= 0.0:
        return False

    timeout_sec = float(getattr(props, "signal_timeout", 0.5))
    return (_now_perf() - last_recv) <= timeout_sec


def _effective_remote_time(scene, props):
    remote_time = float(control_state.get("remote_time", 0.0) or 0.0)
    playback_mode = str(getattr(props, "playback_mode", "BLENDER"))
    remote_transport = str(control_state.get("remote_transport", "unknown"))

    if playback_mode == "BLENDER" and remote_transport == "playing" and _is_signal_fresh(props):
        elapsed = _now_perf() - float(control_state.get("last_time_recv_perf", 0.0) or 0.0)
        return remote_time + elapsed

    return remote_time


def _format_timecode(seconds, scene):
    fps = transport_sync.get_scene_fps(scene)
    if fps <= 0.0:
        fps = 24.0

    safe_seconds = max(0.0, float(seconds))
    total_frames = int(safe_seconds * fps)

    fps_int = max(1, int(round(fps)))
    frames = total_frames % fps_int

    total_seconds = total_frames // fps_int
    secs = total_seconds % 60
    mins = (total_seconds // 60) % 60
    hours = total_seconds // 3600

    return f"{hours:02d}:{mins:02d}:{secs:02d}:{frames:02d}"


def _update_marker_popup(scene):
    global _previous_local_frame, _active_marker_popup_text, _popup_expire_perf

    current_frame = int(getattr(scene, "frame_current", 0))

    if _previous_local_frame is None:
        _previous_local_frame = current_frame
        return

    if current_frame == _previous_local_frame:
        return

    markers = getattr(scene.timeline_markers, "values", None)
    if markers is None:
        marker_list = list(scene.timeline_markers)
    else:
        marker_list = list(scene.timeline_markers.values())

    crossed = []

    if current_frame > _previous_local_frame:
        start = _previous_local_frame
        end = current_frame
        for marker in marker_list:
            marker_frame = int(getattr(marker, "frame", 0))
            if start < marker_frame <= end:
                crossed.append(marker)

        if crossed:
            marker = max(crossed, key=lambda m: int(getattr(m, "frame", 0)))
            _active_marker_popup_text = f"● {getattr(marker, 'name', '')}"
            _popup_expire_perf = _now_perf() + _POPUP_DURATION_SEC

    else:
        start = _previous_local_frame
        end = current_frame
        for marker in marker_list:
            marker_frame = int(getattr(marker, "frame", 0))
            if end <= marker_frame < start:
                crossed.append(marker)

        if crossed:
            marker = min(crossed, key=lambda m: int(getattr(m, "frame", 0)))
            _active_marker_popup_text = f"● {getattr(marker, 'name', '')}"
            _popup_expire_perf = _now_perf() + _POPUP_DURATION_SEC

    _previous_local_frame = current_frame


def _get_overlay_lines(scene, props):
    _update_marker_popup(scene)

    timecode = None
    if bool(getattr(props, "overlay_show_timecode", True)):
        timecode = _format_timecode(_effective_remote_time(scene, props), scene)

    secondary_lines = []

    if bool(getattr(props, "overlay_show_marker_popup", True)):
        if _active_marker_popup_text and _now_perf() <= _popup_expire_perf:
            secondary_lines.append(_active_marker_popup_text)

    if bool(getattr(props, "overlay_show_sync_status", True)):
        sync_status = str(control_state.get("sync_status", "NO_SIGNAL"))
        if sync_status in {"NO_SIGNAL", "DRIFT", "RESYNC", "OUT_OF_RANGE"}:
            secondary_lines.append(f"Sync: {sync_status}")

    if bool(getattr(props, "overlay_show_remote_transport", False)):
        secondary_lines.append(f"Remote Transport: {control_state.get('remote_transport', 'unknown')}")

    if bool(getattr(props, "overlay_show_remote_time_raw", False)):
        secondary_lines.append(f"Raw Remote Time: {float(control_state.get('remote_time', 0.0) or 0.0):.3f}s")

    if bool(getattr(props, "overlay_show_signal_age", False)):
        last_recv = float(control_state.get("last_time_recv_perf", 0.0) or 0.0)
        age = (_now_perf() - last_recv) if last_recv > 0.0 else -1.0
        secondary_lines.append("Signal Age: n/a" if age < 0.0 else f"Signal Age: {age:.3f}s")

    if bool(getattr(props, "overlay_show_desync", False)):
        secondary_lines.append(
            f"Desync: {float(control_state.get('desync_frames', 0.0) or 0.0):.2f} fr / "
            f"{float(control_state.get('desync_sec', 0.0) or 0.0):.4f}s"
        )

    if bool(getattr(props, "overlay_show_playback_mode", False)):
        mode = control_state.get("active_playback_mode", getattr(props, "playback_mode", "BLENDER"))
        secondary_lines.append(f"Playback Mode: {mode}")

    if bool(getattr(props, "overlay_show_push_guard_state", False)):
        secondary_lines.append(f"Push Guard: {control_state.get('push_guard_state', 'NORMAL')}")

    if bool(getattr(props, "overlay_show_last_error", False)):
        last_error = str(control_state.get("last_error", "") or "")
        if last_error:
            secondary_lines.append(f"Last Error: {last_error}")

    return timecode, secondary_lines


def _draw_text(x, y, text, size):
    font_id = 0
    shadow_offset = 1

    blf.size(font_id, int(size))
    blf.color(font_id, 0.0, 0.0, 0.0, 1.0)
    blf.position(font_id, x + shadow_offset, y - shadow_offset, 0)
    blf.draw(font_id, text)

    blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
    blf.position(font_id, x, y, 0)
    blf.draw(font_id, text)


def _draw_overlay(context, target):
    scene, props = _get_scene_and_props(context)
    if scene is None or props is None:
        return

    if not bool(getattr(props, "overlay_enabled", True)):
        return

    if not bool(getattr(props, "sync_enabled", False)):
        return

    if target == "VIEW_3D" and not bool(getattr(props, "overlay_in_viewport", True)):
        return

    if target == "SEQUENCE_EDITOR" and not bool(getattr(props, "overlay_in_vse_preview", True)):
        return

    area = getattr(context, "area", None)
    region = getattr(context, "region", None)
    if area is None or region is None:
        return

    if target == "SEQUENCE_EDITOR":
        if area.type != "SEQUENCE_EDITOR":
            return

        if region.type != "PREVIEW":
            return

    timecode, secondary_lines = _get_overlay_lines(scene, props)
    if not timecode and not secondary_lines:
        return

    margin_x = int(getattr(props, "overlay_margin_x", 20))
    margin_y = int(getattr(props, "overlay_margin_y", 40))
    base_size = int(getattr(props, "overlay_font_size", 16))

    x = margin_x
    y = margin_y

    if timecode:
        timecode_size = max(12, int(round(base_size * 1.6)))
        _draw_text(x, y, timecode, timecode_size)
        y += timecode_size + 6

    for line in secondary_lines:
        _draw_text(x, y, line, base_size)
        y += base_size + 4


def _draw_view3d_overlay():
    _draw_overlay(bpy.context, "VIEW_3D")


def _draw_vse_overlay():
    _draw_overlay(bpy.context, "SEQUENCE_EDITOR")


def tag_redraw_areas():
    context = bpy.context
    wm = getattr(context, "window_manager", None)
    if wm is None:
        return

    for window in wm.windows:
        screen = getattr(window, "screen", None)
        if screen is None:
            continue

        for area in screen.areas:
            if area.type in {"VIEW_3D", "SEQUENCE_EDITOR"}:
                area.tag_redraw()


def register_draw_handlers():
    global _VIEW3D_HANDLE, _VSE_HANDLE

    if _VIEW3D_HANDLE is None:
        _VIEW3D_HANDLE = SpaceView3D.draw_handler_add(_draw_view3d_overlay, (), "WINDOW", "POST_PIXEL")

    if _VSE_HANDLE is None:
        _VSE_HANDLE = SpaceSequenceEditor.draw_handler_add(_draw_vse_overlay, (), "WINDOW", "POST_PIXEL")


def unregister_draw_handlers():
    global _VIEW3D_HANDLE, _VSE_HANDLE

    if _VIEW3D_HANDLE is not None:
        try:
            SpaceView3D.draw_handler_remove(_VIEW3D_HANDLE, "WINDOW")
        except Exception:
            pass
        _VIEW3D_HANDLE = None

    if _VSE_HANDLE is not None:
        try:
            SpaceSequenceEditor.draw_handler_remove(_VSE_HANDLE, "WINDOW")
        except Exception:
            pass
        _VSE_HANDLE = None


def register():
    register_draw_handlers()


def unregister():
    global _previous_local_frame, _active_marker_popup_text, _popup_expire_perf

    unregister_draw_handlers()
    _previous_local_frame = None
    _active_marker_popup_text = ""
    _popup_expire_perf = 0.0
