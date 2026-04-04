#__init__.py

bl_info = {
    "name": "VSE Stem Exporter",
    "author": "InfameDavid",
    "version": (1, 1, 2),
    "blender": (5, 0, 0),
    "location": "Sequence Editor > Sidebar",
    "description": "Export VSE audio master and separate track stems by channel",
    "category": "Sequencer",
}

import bpy
from bpy.app.handlers import persistent

from .properties import VSESE_ExportProperties
from .operators import (
    VSESE_OT_scan_audio_tracks,
    VSESE_OT_export_audio_batch,
    VSESE_OT_reset_status,
)
from .ui import VSESE_PT_main_panel
from .utils_audio import reset_runtime_state


classes = (
    VSESE_ExportProperties,
    VSESE_OT_scan_audio_tracks,
    VSESE_OT_export_audio_batch,
    VSESE_OT_reset_status,
    VSESE_PT_main_panel,
)


@persistent
def vsese_load_post(_dummy):
    """
    Se ejecuta después de cargar un .blend, ya fuera del contexto restringido.
    Aquí sí es seguro tocar bpy.data.scenes.
    """
    for scene in bpy.data.scenes:
        if hasattr(scene, "vsese_export") and scene.vsese_export:
            reset_runtime_state(scene.vsese_export)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.vsese_export = bpy.props.PointerProperty(
        type=VSESE_ExportProperties
    )

    if vsese_load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(vsese_load_post)


def unregister():
    if vsese_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(vsese_load_post)

    if hasattr(bpy.types.Scene, "vsese_export"):
        del bpy.types.Scene.vsese_export

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)