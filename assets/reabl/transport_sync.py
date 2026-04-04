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
    if screen is None:
        return False

    return bool(screen.is_animation_playing)


def ensure_playing(context=None):
    if context is None:
        context = bpy.context

    screen = context.screen
    if screen is None:
        return False

    if not screen.is_animation_playing:
        bpy.ops.screen.animation_play()
        return True

    return False


def ensure_stopped(context=None):
    if context is None:
        context = bpy.context

    screen = context.screen
    if screen is None:
        return False

    if screen.is_animation_playing:
        bpy.ops.screen.animation_cancel(restore_frame=False)
        return True

    return False


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