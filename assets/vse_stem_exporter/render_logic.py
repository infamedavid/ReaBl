#render_logic.py

import bpy

from .utils_audio import (
    get_audio_channels,
    build_export_basename,
    get_extension_for_format,
    build_track_output_filepath,
    build_master_output_filepath,
    snapshot_strip_mute_states,
    restore_strip_mute_states,
    get_render_frame_range,
    set_status,
    solo_channel_from_grouped,
    restore_full_mix,
    file_conflicts,
)


def get_mixdown_settings(props):
    """
    Devuelve container / codec / sample format para bpy.ops.sound.mixdown
    """
    audio_format = props.audio_format

    if audio_format == 'WAV':
        return {
            "container": 'WAV',
            "codec": 'PCM',
            "format": 'S16',
        }

    # fallback defensivo
    return {
        "container": 'WAV',
        "codec": 'PCM',
        "format": 'S16',
    }


def run_audio_mixdown(scene, props, output_filepath):
    """
    Exporta audio puro usando bpy.ops.sound.mixdown, no render de video.
    """
    mix = get_mixdown_settings(props)

    frame_start, frame_end = get_render_frame_range(scene, props.use_preview_range)

    bpy.ops.sound.mixdown(
        filepath=output_filepath,
        check_existing=False,
        accuracy=1024,
        container=mix["container"],
        codec=mix["codec"],
        format=mix["format"],
        split_channels=False,
    )


def execute_audio_batch(context):
    scene = context.scene
    props = scene.vsese_export

    channels, grouped = get_audio_channels(
        scene,
        skip_muted=props.skip_muted_strips,
    )

    props.detected_track_count = len(channels)
    props.detected_track_list = ", ".join(str(ch) for ch in channels)

    total_tasks = 0
    if props.export_tracks:
        total_tasks += len(channels)
    if props.export_master:
        total_tasks += 1

    props.total_tasks = total_tasks
    props.completed_tasks = 0
    props.progress = 0.0

    basename = build_export_basename(scene, props)
    ext = get_extension_for_format(props.audio_format)

    mute_snapshot = snapshot_strip_mute_states(scene)
    completed = 0

    try:
        if props.export_tracks:
            for index, channel in enumerate(channels, start=1):
                filepath = build_track_output_filepath(
                    props.output_dir,
                    basename,
                    channel,
                    ext,
                )

                if file_conflicts(filepath) and not props.overwrite_existing:
                    raise RuntimeError(
                        f"File already exists and overwrite is disabled: {filepath}"
                    )

                set_status(
                    props,
                    text=f"Rendering track {index}/{len(channels)} (Channel {channel})",
                    completed=completed,
                    total=total_tasks,
                )

                solo_channel_from_grouped(scene, grouped, channel)
                run_audio_mixdown(scene, props, filepath)

                completed += 1
                set_status(
                    props,
                    text=f"Finished track {channel}",
                    completed=completed,
                    total=total_tasks,
                )

        if props.export_master:
            filepath = build_master_output_filepath(
                props.output_dir,
                basename,
                ext,
            )

            if file_conflicts(filepath) and not props.overwrite_existing:
                raise RuntimeError(
                    f"File already exists and overwrite is disabled: {filepath}"
                )

            restore_full_mix(mute_snapshot)

            set_status(
                props,
                text="Rendering master",
                completed=completed,
                total=total_tasks,
            )

            run_audio_mixdown(scene, props, filepath)

            completed += 1
            set_status(
                props,
                text="Finished master",
                completed=completed,
                total=total_tasks,
            )

    finally:
        restore_strip_mute_states(mute_snapshot)

    set_status(
        props,
        text="Done",
        completed=completed,
        total=total_tasks,
    )