# ops_python_osc.py

import subprocess
import sys

import bpy

from .constants import LIB_NAME
from .utils import is_library_installed


class REABLSETUP_OT_InstallPythonOSC(bpy.types.Operator):
    """Install python-osc into Blender's Python environment"""
    bl_idname = "reabl_setup.install_python_osc"
    bl_label = "Install python-osc"
    bl_description = f"Install '{LIB_NAME}' for this Blender version"

    @classmethod
    def poll(cls, context):
        return not is_library_installed()

    def execute(self, context):
        self.report({'INFO'}, f"Installing '{LIB_NAME}'. Blender may freeze for a moment.")
        try:
            python_exe = sys.executable
            subprocess.check_call(
                [python_exe, "-m", "pip", "install", LIB_NAME],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.report({'INFO'}, f"'{LIB_NAME}' installed. Please restart Blender.")
        except Exception as e:
            self.report({'ERROR'}, f"Install failed. Run Blender as admin/sudo. Error: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}


class REABLSETUP_OT_UninstallPythonOSC(bpy.types.Operator):
    """Uninstall python-osc from Blender's Python environment"""
    bl_idname = "reabl_setup.uninstall_python_osc"
    bl_label = "Uninstall python-osc"
    bl_description = f"Remove '{LIB_NAME}' from this Blender version"

    @classmethod
    def poll(cls, context):
        return is_library_installed()

    def execute(self, context):
        self.report({'INFO'}, f"Uninstalling '{LIB_NAME}'...")
        try:
            python_exe = sys.executable
            subprocess.check_call(
                [python_exe, "-m", "pip", "uninstall", LIB_NAME, "-y"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.report({'INFO'}, f"'{LIB_NAME}' uninstalled. Please restart Blender.")
        except Exception as e:
            self.report({'ERROR'}, f"Uninstall failed. Error: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}


classes = (
    REABLSETUP_OT_InstallPythonOSC,
    REABLSETUP_OT_UninstallPythonOSC,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)