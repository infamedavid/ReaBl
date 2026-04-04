import bpy
from bpy.types import Panel


class VSESE_PT_main_panel(Panel):
    bl_label = "VSE Stem Exporter"
    bl_idname = "VSESE_PT_main_panel"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "VSE Export"

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.vsese_export

        # Output
        box = layout.box()
        box.label(text="Output")
        box.prop(props, "output_dir")
        box.prop(props, "use_scene_name")

        row = box.row()
        row.enabled = not props.use_scene_name
        row.prop(props, "base_name")

        box.prop(props, "overwrite_existing")

        # Export options
        box = layout.box()
        box.label(text="Export Options")
        box.prop(props, "export_master")
        box.prop(props, "export_tracks")
        #box.prop(props, "only_tracks_with_audio")
        box.prop(props, "skip_muted_strips")
        box.prop(props, "use_preview_range")

        # Audio format
        box = layout.box()
        box.label(text="Audio Format")
        box.prop(props, "audio_format")
        box.prop(props, "sample_rate")
        box.prop(props, "audio_channels")

        # Scan summary
        box = layout.box()
        box.label(text="Scan Summary")
        box.label(text=f"Detected Tracks: {props.detected_track_count}")
        box.label(text=f"Channels: {props.detected_track_list or '-'}")
        box.label(text=f"Total Tasks: {props.total_tasks}")

        # Progress
        box = layout.box()
        box.label(text="Progress")
        box.prop(props, "progress", text="")
        box.label(text=f"Status: {props.status_text}")

        if props.last_error and props.status_text.startswith("Error:"):
            col = box.column()
            col.alert = True
            col.label(text=f"Error: {props.last_error}")

        # Buttons
        row = layout.row(align=True)
        row.operator("vsese.scan_audio_tracks", icon='VIEWZOOM')
        row.operator("vsese.reset_status", icon='LOOP_BACK')

        row = layout.row()
        row.enabled = not props.is_rendering
        row.scale_y = 1.4
        row.operator("vsese.export_audio_batch", icon='RENDER_ANIMATION')