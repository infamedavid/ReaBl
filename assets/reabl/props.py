# props.py

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty
from bpy.types import PropertyGroup


class REABL_Properties(PropertyGroup):
    sync_enabled: BoolProperty(
        name="Sync Enabled",
        description="Enable REAPER to Blender sync",
        default=False,
    )

    osc_port: IntProperty(
        name="OSC Port",
        description="Port used by Blender to receive OSC from REAPER",
        default=9000,
        min=1,
        max=65535,
    )

    playback_mode: EnumProperty(
        name="Playback Mode",
        description="Choose whether Blender uses its own playback or follows pushed external timecode",
        items=(
            ("BLENDER", "Blender Playback", "Use Blender internal playback and drift correction"),
            ("PUSH", "Push Playback", "Keep Blender stopped and push the playhead from external timecode"),
        ),
        default="PUSH",
    )

    soft_desync_frames: FloatProperty(
        name="Soft Drift",
        description="Frames of error before drift state is reported",
        default=1.0,
        min=0.0,
    )

    hard_desync_frames: FloatProperty(
        name="Hard Resync",
        description="Frames of error before Blender is forced back into sync",
        default=3.0,
        min=0.0,
    )

    signal_timeout: FloatProperty(
        name="Signal Timeout",
        description="Seconds without /reabl/state/time before signal is considered lost",
        default=0.5,
        min=0.01,
    )

    overlay_enabled: BoolProperty(
        name="Overlay",
        description="Show sync status overlay",
        default=True,
    )


    overlay_in_viewport: BoolProperty(
        name="3D View",
        description="Draw overlay in the 3D View",
        default=True,
    )

    overlay_in_vse_preview: BoolProperty(
        name="VSE Preview",
        description="Draw overlay in the Video Sequence Editor preview",
        default=True,
    )

    overlay_font_size: IntProperty(
        name="Font Size",
        description="Base font size for overlay text",
        default=16,
        min=8,
        max=72,
    )

    overlay_margin_x: IntProperty(
        name="Margin X",
        description="Horizontal margin from bottom-left",
        default=20,
        min=0,
        max=2000,
    )

    overlay_margin_y: IntProperty(
        name="Margin Y",
        description="Vertical margin from bottom-left",
        default=40,
        min=0,
        max=2000,
    )

    overlay_show_timecode: BoolProperty(
        name="Timecode",
        description="Show main remote timecode line",
        default=True,
    )

    overlay_show_marker_popup: BoolProperty(
        name="Marker Popup",
        description="Show temporary popup for crossed local Blender markers",
        default=True,
    )

    overlay_show_sync_status: BoolProperty(
        name="Sync Problems",
        description="Show sync status only when there is a sync problem",
        default=True,
    )

    overlay_show_remote_transport: BoolProperty(
        name="Remote Transport",
        description="Debug: show remote transport state",
        default=False,
    )

    overlay_show_remote_time_raw: BoolProperty(
        name="Raw Remote Time",
        description="Debug: show raw remote time received",
        default=False,
    )

    overlay_show_signal_age: BoolProperty(
        name="Signal Age",
        description="Debug: show age of latest remote time signal",
        default=False,
    )

    overlay_show_desync: BoolProperty(
        name="Desync",
        description="Debug: show desync in frames and seconds",
        default=False,
    )

    overlay_show_playback_mode: BoolProperty(
        name="Playback Mode",
        description="Debug: show active playback mode",
        default=False,
    )

    overlay_show_push_guard_state: BoolProperty(
        name="Push Guard",
        description="Debug: show push guard state",
        default=False,
    )

    overlay_show_last_error: BoolProperty(
        name="Last Error",
        description="Debug: show last runtime error",
        default=False,
    )


def register():
    bpy.utils.register_class(REABL_Properties)
    bpy.types.Scene.reabl = PointerProperty(type=REABL_Properties)


def unregister():
    del bpy.types.Scene.reabl
    bpy.utils.unregister_class(REABL_Properties)