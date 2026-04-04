#properties.py

import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    StringProperty,
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
)


class VSESE_ExportProperties(PropertyGroup):
    # Output
    output_dir: StringProperty(
        name="Output Folder",
        subtype='DIR_PATH',
        default="",
    )

    base_name: StringProperty(
        name="Base Name",
        default="",
    )

    use_scene_name: BoolProperty(
        name="Use Scene Name",
        default=True,
    )

    overwrite_existing: BoolProperty(
        name="Overwrite Existing",
        default=False,
    )

    # Export scope
    export_master: BoolProperty(
        name="Export Master",
        default=True,
    )

    export_tracks: BoolProperty(
        name="Export Separate Tracks",
        default=True,
    )

    only_tracks_with_audio: BoolProperty(
        name="Only Tracks With Audio",
        default=True,
    )

    skip_muted_strips: BoolProperty(
        name="Skip Muted Audio Strips",
        default=True,
    )

    use_preview_range: BoolProperty(
        name="Use Preview Range",
        default=True,
    )

    # Audio format
    audio_format: EnumProperty(
        name="Format",
        items=[
            ('WAV', "WAV", "Wave audio"),
        ],
        default='WAV',
    )

    sample_rate: EnumProperty(
        name="Sample Rate",
        items=[
            ('44100', "44100 Hz", ""),
            ('48000', "48000 Hz", ""),
            ('96000', "96000 Hz", ""),
        ],
        default='48000',
    )

    audio_channels: EnumProperty(
        name="Channels",
        items=[
            ('MONO', "Mono", ""),
            ('STEREO', "Stereo", ""),
        ],
        default='STEREO',
    )

    # Runtime / status
    progress: FloatProperty(
        name="Progress",
        min=0.0,
        max=100.0,
        default=0.0,
        subtype='PERCENTAGE',
    )

    status_text: StringProperty(
        name="Status",
        default="Idle",
    )

    total_tasks: IntProperty(
        name="Total Tasks",
        default=0,
        min=0,
    )

    completed_tasks: IntProperty(
        name="Completed Tasks",
        default=0,
        min=0,
    )

    detected_track_count: IntProperty(
        name="Detected Tracks",
        default=0,
        min=0,
    )

    detected_track_list: StringProperty(
        name="Detected Track List",
        default="",
    )

    is_rendering: BoolProperty(
        name="Is Rendering",
        default=False,
    )

    last_error: StringProperty(
        name="Last Error",
        default="",
    )