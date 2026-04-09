# ui.py

import bpy
from bpy.types import Panel

from .state import control_state
from . import osc_server


def draw_reabl_ui(layout, context):
    scene = context.scene
    props = scene.reabl
    playback_mode = getattr(props, "playback_mode", "BLENDER")

    deps_ok = osc_server.dependencies_ok()
    missing = osc_server.get_missing_dependencies()

    if not deps_ok:
        box = layout.box()
        box.alert = True
        box.label(text=osc_server.get_dependency_error_message(), icon='ERROR')

        for dep in missing:
            box.label(text=f"Missing: {dep}", icon='DOT')

        layout.separator()

    # ------------------------------------------------------------
    # Main controls
    # ------------------------------------------------------------
    col = layout.column(align=True)
    col.enabled = deps_ok
    col.prop(props, "sync_enabled")
    col.prop(props, "osc_port")

    layout.separator()

    # ------------------------------------------------------------
    # Thresholds
    # ------------------------------------------------------------
    box = layout.box()
    box.enabled = deps_ok
    box.label(text="Thresholds")

    col = box.column(align=True)
    if playback_mode == "BLENDER":
        col.prop(props, "soft_desync_frames")
        col.prop(props, "hard_desync_frames")
    col.prop(props, "signal_timeout")

    layout.separator()

    # ------------------------------------------------------------
    # Performance
    # ------------------------------------------------------------
    box = layout.box()
    box.label(text="Performance")

    box.prop(scene.render, "use_simplify", text="Simplify Scene")

    sub = box.column(align=True)
    sub.enabled = scene.render.use_simplify

    sub.prop(scene.render, "simplify_subdivision", text="Max Subdivision")
    sub.prop(scene.render, "simplify_child_particles", text="Max Child Particles")
    sub.prop(scene.render, "simplify_volumes", text="Volume Resolution")

    layout.separator()

    # ------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------
    
    box = layout.box()
    box.enabled = deps_ok
    box.label(text="Playback")
    box.prop(props, "playback_mode", text="Mode")

    if playback_mode == "BLENDER":
        box.prop(scene, "sync_mode", text="Sync")

    layout.separator()

    # ------------------------------------------------------------
    # Overlay
    # ------------------------------------------------------------
    box = layout.box()
    box.enabled = deps_ok
    box.label(text="Overlay")

    col = box.column(align=True)
    col.prop(props, "overlay_enabled")
    col.prop(props, "overlay_in_viewport")
    col.prop(props, "overlay_in_vse_preview")
    col.prop(props, "overlay_font_size")
    col.prop(props, "overlay_margin_x")
    col.prop(props, "overlay_margin_y")

    content = box.column(align=True)
    content.label(text="Content")
    content.prop(props, "overlay_show_timecode")
    content.prop(props, "overlay_show_marker_popup")
    content.prop(props, "overlay_show_sync_status")

    debug = box.column(align=True)
    debug.label(text="Debug")
    debug.prop(props, "overlay_show_remote_transport")
    debug.prop(props, "overlay_show_remote_time_raw")
    debug.prop(props, "overlay_show_signal_age")
    debug.prop(props, "overlay_show_desync")
    debug.prop(props, "overlay_show_playback_mode")
    debug.prop(props, "overlay_show_push_guard_state")
    debug.prop(props, "overlay_show_last_error")

    layout.separator()

    # ------------------------------------------------------------
    # Runtime status
    # ------------------------------------------------------------
    box = layout.box()
    box.label(text="Runtime Status")

    row = box.row()
    row.label(text="Dependencies:")
    row.label(text="OK" if deps_ok else "Missing")

    row = box.row()
    row.label(text="OSC Running:")
    row.label(text="Yes" if control_state["osc_running"] else "No")

    row = box.row()
    row.label(text="Playback Mode:")
    row.label(text=str(control_state.get("active_playback_mode", playback_mode)))

    if playback_mode == "PUSH":
        row = box.row()
        row.label(text="Push Guard:")
        row.label(text=str(control_state.get("push_guard_state", "NORMAL")))

    row = box.row()
    row.label(text="Remote Transport:")
    row.label(text=str(control_state["remote_transport"]))

    row = box.row()
    row.label(text="Remote Time:")
    row.label(text=f'{control_state["remote_time"]:.3f}s')

    row = box.row()
    row.label(text="Sync Status:")
    row.label(text=str(control_state["sync_status"]))

    row = box.row()
    row.label(text="Desync:")
    row.label(text=f'{control_state["desync_frames"]:.2f} fr')

    row = box.row()
    row.label(text="Local Frame:")
    row.label(text=str(scene.frame_current))

    if control_state.get("last_error"):
        row = box.row()
        row.label(text="Error:")
        row.label(text=str(control_state["last_error"]))


class REABL_PT_main_panel_3d(Panel):
    bl_label = "ReaBL"
    bl_idname = "REABL_PT_main_panel_3d"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ReaBL"

    def draw(self, context):
        draw_reabl_ui(self.layout, context)


class REABL_PT_main_panel_vse(Panel):
    bl_label = "ReaBL"
    bl_idname = "REABL_PT_main_panel_vse"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "ReaBL"

    def draw(self, context):
        draw_reabl_ui(self.layout, context)


classes = (
    REABL_PT_main_panel_3d,
    REABL_PT_main_panel_vse,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)