#utils_audio.py

import os


def get_sequence_editor(scene):
    return getattr(scene, "sequence_editor", None)


def get_all_strips(scene):
    seq = get_sequence_editor(scene)
    if not seq:
        return []

    # Blender 5+
    if hasattr(seq, "strips_all"):
        return list(seq.strips_all)

    # Fallback viejo
    if hasattr(seq, "sequences_all"):
        return list(seq.sequences_all)

    return []


def get_audio_strips(scene, skip_muted=True):
    strips = []
    for strip in get_all_strips(scene):
        if strip.type != 'SOUND':
            continue
        if skip_muted and strip.mute:
            continue
        strips.append(strip)

    return strips


def group_audio_strips_by_channel(strips):
    grouped = {}
    for strip in strips:
        grouped.setdefault(strip.channel, []).append(strip)
    return dict(sorted(grouped.items(), key=lambda item: item[0]))


def get_audio_channels(scene, skip_muted=True):
    strips = get_audio_strips(scene, skip_muted=skip_muted)
    grouped = group_audio_strips_by_channel(strips)
    return list(grouped.keys()), grouped


def build_export_basename(scene, props):
    if props.use_scene_name:
        name = scene.name.strip()
    else:
        name = props.base_name.strip() or scene.name.strip()

    return sanitize_filename(name or "untitled")


def sanitize_filename(name):
    invalid = '<>:"/\\|?*'
    for ch in invalid:
        name = name.replace(ch, "_")
    return name.strip(" ._")


def get_extension_for_format(audio_format):
    mapping = {
        'WAV': ".wav",
    }
    return mapping.get(audio_format, ".wav")


def build_track_output_filepath(output_dir, basename, channel, ext):
    filename = f"{basename}_track_{channel:02d}{ext}"
    return os.path.join(output_dir, filename)


def build_master_output_filepath(output_dir, basename, ext):
    filename = f"{basename}_master{ext}"
    return os.path.join(output_dir, filename)


def path_exists_and_writable(path_dir):
    if not path_dir:
        return False
    if not os.path.isdir(path_dir):
        return False
    return os.access(path_dir, os.W_OK)


def file_conflicts(filepath):
    return os.path.exists(filepath)


def snapshot_strip_mute_states(scene):
    snapshot = []
    for strip in get_all_strips(scene):
        if strip.type == 'SOUND':
            snapshot.append((strip, strip.mute))
    return snapshot


def restore_strip_mute_states(snapshot):
    for strip, mute_state in snapshot:
        try:
            strip.mute = mute_state
        except ReferenceError:
            pass


def snapshot_render_settings(scene):
    render = scene.render
    image = render.image_settings
    ffmpeg = render.ffmpeg

    return {
        "filepath": render.filepath,
        "file_format": image.file_format,
        "ffmpeg_format": getattr(ffmpeg, "format", None),
        "ffmpeg_audio_codec": getattr(ffmpeg, "audio_codec", None),
        "ffmpeg_audio_mixrate": getattr(ffmpeg, "audio_mixrate", None),
        "ffmpeg_audio_channels": getattr(ffmpeg, "audio_channels", None),
        "frame_start": scene.frame_start,
        "frame_end": scene.frame_end,
    }


def restore_render_settings(scene, snapshot):
    render = scene.render
    image = render.image_settings
    ffmpeg = render.ffmpeg

    render.filepath = snapshot["filepath"]
    image.file_format = snapshot["file_format"]

    if snapshot["ffmpeg_format"] is not None:
        ffmpeg.format = snapshot["ffmpeg_format"]
    if snapshot["ffmpeg_audio_codec"] is not None:
        ffmpeg.audio_codec = snapshot["ffmpeg_audio_codec"]
    if snapshot["ffmpeg_audio_mixrate"] is not None:
        ffmpeg.audio_mixrate = snapshot["ffmpeg_audio_mixrate"]
    if snapshot["ffmpeg_audio_channels"] is not None:
        ffmpeg.audio_channels = snapshot["ffmpeg_audio_channels"]

    scene.frame_start = snapshot["frame_start"]
    scene.frame_end = snapshot["frame_end"]


def get_render_frame_range(scene, use_preview_range):
    if use_preview_range:
        start = scene.frame_preview_start
        end = scene.frame_preview_end
        if start < end:
            return start, end

    return scene.frame_start, scene.frame_end


def apply_frame_range(scene, start, end):
    scene.frame_start = start
    scene.frame_end = end


def set_status(props, text, completed=None, total=None):
    props.status_text = text

    if total is not None:
        props.total_tasks = max(0, total)

    if completed is not None:
        props.completed_tasks = max(0, completed)

    if props.total_tasks > 0:
        props.progress = (props.completed_tasks / props.total_tasks) * 100.0
    else:
        props.progress = 0.0


def reset_runtime_state(props):
    props.progress = 0.0
    props.status_text = "Idle"
    props.total_tasks = 0
    props.completed_tasks = 0
    props.detected_track_count = 0
    props.detected_track_list = ""
    props.is_rendering = False
    props.last_error = ""


def validate_export_context(scene, props):
    if not props.output_dir.strip():
        return False, "Output folder is empty."

    if not path_exists_and_writable(props.output_dir):
        return False, "Output folder does not exist or is not writable."

    if not (props.export_tracks or props.export_master):
        return False, "Enable Export Master, Export Separate Tracks, or both."

    seq = get_sequence_editor(scene)
    if not seq:
        return False, "Scene has no sequence editor."

    strips = get_audio_strips(scene, skip_muted=props.skip_muted_strips)
    if not strips:
        return False, "No eligible audio strips found."

    return True, ""


def mute_all_audio(scene):
    for strip in get_all_strips(scene):
        if strip.type == 'SOUND':
            strip.mute = True


def solo_channel_from_grouped(scene, grouped_strips, target_channel):
    mute_all_audio(scene)

    target = grouped_strips.get(target_channel, [])
    for strip in target:
        strip.mute = False


def restore_full_mix(snapshot):
    restore_strip_mute_states(snapshot)