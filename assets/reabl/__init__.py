#__init__.py

bl_info = {
    "name": "ReaBL",
    "author": "InfameDavid",
    "version": (1, 1, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > ReaBL",
    "description": "Seamless REAPER and Blender integration for scoring, playback synchronization, and real-time creative control.",
    "category": "Animation",
}

import importlib

if "state" in locals():
    importlib.reload(state)
    importlib.reload(props)
    importlib.reload(transport_sync)
    importlib.reload(osc_server)
    importlib.reload(sync_timer)
    importlib.reload(overlay)
    importlib.reload(ui)
else:
    from . import state
    from . import props
    from . import transport_sync
    from . import osc_server
    from . import sync_timer
    from . import overlay
    from . import ui


modules = (
    state,
    props,
    transport_sync,
    osc_server,
    sync_timer,
    overlay,
    ui,
)


def register():
    for module in modules:
        if hasattr(module, "register"):
            module.register()


def unregister():
    for module in reversed(modules):
        if hasattr(module, "unregister"):
            module.unregister()