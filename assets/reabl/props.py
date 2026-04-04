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


def register():
    bpy.utils.register_class(REABL_Properties)
    bpy.types.Scene.reabl = PointerProperty(type=REABL_Properties)


def unregister():
    del bpy.types.Scene.reabl
    bpy.utils.unregister_class(REABL_Properties)