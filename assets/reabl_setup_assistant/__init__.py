# __init__.py

bl_info = {
    "name": "ReaBL Setup Assistant",
    "author": "InfameDavid",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "Preferences > Add-ons",
    "description": "Installs python-osc and copies the ReaBL.ReaperOSC config file to REAPER's OSC folder.",
    "category": "System",
}

if "bpy" in locals():
    import importlib
    importlib.reload(constants)
    importlib.reload(utils)
    importlib.reload(ops_python_osc)
    importlib.reload(ops_reaper_config)
    importlib.reload(preferences)
else:
    from . import constants
    from . import utils
    from . import ops_python_osc
    from . import ops_reaper_config
    from . import preferences

import bpy

classes = (
    *ops_python_osc.classes,
    *ops_reaper_config.classes,
    *preferences.classes,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()