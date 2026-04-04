# preferences.py

import os

import bpy

from .constants import ADDON_PACKAGE, LIB_NAME, REAPER_OSC_FILENAME
from .utils import (
    get_installed_reaper_osc_path,
    get_library_version,
    get_packaged_reaper_osc_path,
    is_library_installed,
    normalize_dir_path,
)


class REABLSETUP_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_PACKAGE

    reaper_osc_folder: bpy.props.StringProperty(
        name="REAPER OSC Folder",
        description="Folder where REAPER stores OSC pattern config files",
        subtype='DIR_PATH',
        default="",
    )

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="Python OSC", icon='CONSOLE')

        is_installed = is_library_installed()
        col = box.column(align=True)
        if is_installed:
            version = get_library_version(LIB_NAME)
            col.label(text=f"Status: '{LIB_NAME}' is installed.", icon='CHECKMARK')
            col.label(text=f"Version: {version}", icon='INFO')
        else:
            col.label(text=f"Status: '{LIB_NAME}' is not installed.", icon='ERROR')
            col.label(text="Run Blender as admin/sudo if installation fails.", icon='INFO')

        row = box.row()
        row.active = not is_installed
        row.operator("reabl_setup.install_python_osc", icon='ADD')

        row = box.row()
        row.active = is_installed
        row.operator("reabl_setup.uninstall_python_osc", icon='REMOVE')

        box = layout.box()
        box.label(text="REAPER OSC Config", icon='FILE_FOLDER')
        box.label(text="Select REAPER's OSC folder, then copy the config file.", icon='INFO')
        box.prop(self, "reaper_osc_folder", text="OSC Folder")
        box.operator("reabl_setup.select_reaper_osc_folder", icon='FILE_FOLDER')

        normalized_folder = normalize_dir_path(self.reaper_osc_folder)
        packaged_path = get_packaged_reaper_osc_path()

        if not normalized_folder:
            box.label(text="No OSC folder selected.", icon='ERROR')
        elif os.path.isdir(normalized_folder):
            box.label(text="OSC folder ready.", icon='CHECKMARK')
        else:
            box.label(text="Selected OSC folder not found.", icon='ERROR')

        if os.path.isfile(packaged_path):
            box.label(text=f"Packaged file: {REAPER_OSC_FILENAME}", icon='FILE')
        else:
            box.label(text="Packaged ReaBL.ReaperOSC file not found.", icon='ERROR')

        installed_path = get_installed_reaper_osc_path(context)
        if installed_path and os.path.isfile(installed_path):
            box.label(text=f"{REAPER_OSC_FILENAME} is already present in the selected folder.", icon='CHECKMARK')
        elif normalized_folder and os.path.isdir(normalized_folder):
            box.label(text=f"{REAPER_OSC_FILENAME} is not yet installed in the selected folder.", icon='INFO')

        row = box.row()
        row.active = bool(normalized_folder) and os.path.isdir(normalized_folder) and os.path.isfile(packaged_path)
        row.operator("reabl_setup.copy_reaper_osc_config", icon='COPYDOWN')


classes = (
    REABLSETUP_AddonPreferences,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)