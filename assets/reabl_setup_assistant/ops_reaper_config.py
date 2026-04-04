# ops_reaper_config.py

import os
import shutil

import bpy

from .constants import REAPER_OSC_FILENAME
from .utils import (
    get_packaged_reaper_osc_path,
    get_selected_osc_folder,
)


class REABLSETUP_OT_CopyReaperOSCConfig(bpy.types.Operator):
    """Copy the packaged ReaBL.ReaperOSC file into the selected REAPER OSC folder"""
    bl_idname = "reabl_setup.copy_reaper_osc_config"
    bl_label = "Copy ReaBL.ReaperOSC"
    bl_description = "Copy the packaged ReaBL.ReaperOSC file into the selected REAPER OSC folder"

    def execute(self, context):
        osc_folder = get_selected_osc_folder(context)
        if not osc_folder:
            self.report({'ERROR'}, "No OSC folder selected.")
            return {'CANCELLED'}

        if not os.path.isdir(osc_folder):
            self.report({'ERROR'}, "Selected OSC folder not found.")
            return {'CANCELLED'}

        source_path = get_packaged_reaper_osc_path()
        if not os.path.isfile(source_path):
            self.report({'ERROR'}, "Packaged ReaBL.ReaperOSC file not found.")
            return {'CANCELLED'}

        destination_path = os.path.join(osc_folder, REAPER_OSC_FILENAME)
        existed_before = os.path.isfile(destination_path)

        try:
            shutil.copy2(source_path, destination_path)
        except Exception as e:
            self.report({'ERROR'}, f"Could not copy ReaBL.ReaperOSC. Error: {e}")
            return {'CANCELLED'}

        if existed_before:
            self.report({'INFO'}, "Existing ReaBL.ReaperOSC updated successfully.")
        else:
            self.report({'INFO'}, "ReaBL.ReaperOSC copied successfully.")

        return {'FINISHED'}


classes = (
    REABLSETUP_OT_CopyReaperOSCConfig,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)