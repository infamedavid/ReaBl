#operators.py

import bpy
from bpy.types import Operator

from .utils_audio import (
    get_audio_channels,
    reset_runtime_state,
    set_status,
    validate_export_context,
)
from .render_logic import execute_audio_batch


class VSESE_OT_scan_audio_tracks(Operator):
    bl_idname = "vsese.scan_audio_tracks"
    bl_label = "Scan Audio Tracks"
    bl_description = "Scan VSE audio strips and detect occupied channels"

    def execute(self, context):
        scene = context.scene
        props = scene.vsese_export

        # Limpieza previa para no arrastrar errores viejos
        reset_runtime_state(props)

        channels, _grouped = get_audio_channels(
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
        props.last_error = ""

        set_status(
            props,
            text=f"Detected {len(channels)} track(s)",
            completed=0,
            total=total_tasks,
        )

        self.report({'INFO'}, f"Detected channels: {props.detected_track_list or 'None'}")
        return {'FINISHED'}


class VSESE_OT_export_audio_batch(Operator):
    bl_idname = "vsese.export_audio_batch"
    bl_label = "Export Audio"
    bl_description = "Export master and/or separate VSE audio tracks by channel"

    def execute(self, context):
        scene = context.scene
        props = scene.vsese_export

        if props.is_rendering:
            self.report({'WARNING'}, "Export already in progress.")
            return {'CANCELLED'}

        # Limpieza previa para que no quede basura vieja en UI
        props.last_error = ""
        props.progress = 0.0
        props.completed_tasks = 0
        props.total_tasks = 0
        props.status_text = "Validating..."
        props.is_rendering = True

        try:
            ok, message = validate_export_context(scene, props)
            if not ok:
                props.last_error = message
                set_status(props, f"Error: {message}", completed=0, total=0)
                self.report({'ERROR'}, message)
                return {'CANCELLED'}

            set_status(props, "Scanning tracks...", completed=0, total=0)
            execute_audio_batch(context)

        except Exception as ex:
            props.last_error = str(ex)
            set_status(props, f"Error: {ex}", completed=0, total=props.total_tasks)
            self.report({'ERROR'}, str(ex))
            return {'CANCELLED'}

        finally:
            props.is_rendering = False

        self.report({'INFO'}, "Audio export finished.")
        return {'FINISHED'}


class VSESE_OT_reset_status(Operator):
    bl_idname = "vsese.reset_status"
    bl_label = "Reset Status"
    bl_description = "Reset progress and status fields"

    def execute(self, context):
        props = context.scene.vsese_export
        reset_runtime_state(props)
        self.report({'INFO'}, "Status reset.")
        return {'FINISHED'}