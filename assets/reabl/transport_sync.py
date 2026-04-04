# transport_sync.py

import bpy


def get_scene_fps(scene=None):
    if scene is None:
        scene = bpy.context.scene

    render = scene.render
    if render.fps_base == 0:
        return float(render.fps)

    return float(render.fps) / float(render.fps_base)


def get_local_frame(scene=None):
    if scene is None:
        scene = bpy.context.scene
    return float(scene.frame_current)


def get_local_time_seconds(scene=None):
    if scene is None:
        scene = bpy.context.scene

    fps = get_scene_fps(scene)
    if fps <= 0.0:
        return 0.0

    return float(scene.frame_current) / fps


def time_to_frame(seconds, scene=None):
    if scene is None:
        scene = bpy.context.scene

    fps = get_scene_fps(scene)
    return int(round(float(seconds) * fps))


def frame_to_time(frame, scene=None):
    if scene is None:
        scene = bpy.context.scene

    fps = get_scene_fps(scene)
    if fps <= 0.0:
        return 0.0

    return float(frame) / fps


def get_animation_range(scene=None):
    if scene is None:
        scene = bpy.context.scene

    return int(scene.frame_start), int(scene.frame_end)


def is_frame_in_animation_range(frame, scene=None):
    if scene is None:
        scene = bpy.context.scene

    start_frame, end_frame = get_animation_range(scene)
    frame = int(round(frame))
    return start_frame <= frame <= end_frame


def set_frame_if_needed(target_frame, scene=None):
    if scene is None:
        scene = bpy.context.scene

    target_frame = int(round(target_frame))

    if scene.frame_current != target_frame:
        scene.frame_set(target_frame)
        return True

    return False


def is_animation_playing(context=None):
    if context is None:
        context = bpy.context

    screen = context.screen
    if screen is not None:
        return bool(screen.is_animation_playing)

    wm = getattr(context, "window_manager", None) or getattr(bpy.context, "window_manager", None)
    if wm is None:
        return False

    for window in wm.windows:
        win_screen = getattr(window, "screen", None)
        if win_screen is not None and bool(win_screen.is_animation_playing):
            return True

    return False


def _iter_transport_overrides(context=None):
    if context is None:
        context = bpy.context

    wm = getattr(context, "window_manager", None) or getattr(bpy.context, "window_manager", None)
    if wm is None:
        return

    for window in wm.windows:
        screen = getattr(window, "screen", None)
        if screen is None:
            continue

        yielded_screen_level = False

        for area in screen.areas:
            region = None
            for candidate in area.regions:
                if candidate.type == "WINDOW":
                    region = candidate
                    break

            if region is None:
                continue

            yielded_screen_level = True
            yield {"window": window, "screen": screen, "area": area, "region": region}

        if not yielded_screen_level:
            yield {"window": window, "screen": screen}


def _run_transport_operator(op_callable, context=None, **kwargs):
    for override in _iter_transport_overrides(context):
        try:
            with bpy.context.temp_override(**override):
                if not op_callable.poll():
                    continue

                op_callable(**kwargs)
                return True
        except Exception:
            continue

    return False


def ensure_playing(context=None):
    if context is None:
        context = bpy.context

    was_playing = is_animation_playing(context)
    if was_playing:
        return False

    _run_transport_operator(bpy.ops.screen.animation_play, context)
    is_playing_now = is_animation_playing(context)
    if not is_playing_now:
        return False

    return not was_playing and is_playing_now


def ensure_stopped(context=None):
    if context is None:
        context = bpy.context

    was_playing = is_animation_playing(context)
    if not was_playing:
        return False

    _run_transport_operator(
        bpy.ops.screen.animation_cancel,
        context,
        restore_frame=False,
    )
    is_playing_now = is_animation_playing(context)
    if is_playing_now:
        return False

    return was_playing and not is_playing_now


def ensure_paused(context=None):
    return ensure_stopped(context)


def hard_resync_to_frame(target_frame, scene=None, context=None):
    if scene is None:
        scene = bpy.context.scene

    return set_frame_if_needed(target_frame, scene)


def register():
    pass


def unregister():
    pass
