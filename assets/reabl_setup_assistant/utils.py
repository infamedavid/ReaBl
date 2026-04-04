# utils.py

import os
import importlib
import importlib.util
import importlib.metadata

import bpy

from .constants import ADDON_PACKAGE, LIB_NAME, MODULE_NAME, REAPER_OSC_FILENAME


def is_library_installed() -> bool:
    try:
        spec = importlib.util.find_spec(MODULE_NAME)
        return spec is not None
    except (ImportError, ModuleNotFoundError):
        return False


def get_library_version(name: str = LIB_NAME) -> str:
    try:
        importlib.reload(importlib.metadata)
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "Unknown"
    except Exception:
        return "Unknown"


def get_addon_preferences(context=None):
    if context is None:
        context = bpy.context

    addons = getattr(context.preferences, "addons", None)
    if addons is None:
        return None

    addon = addons.get(ADDON_PACKAGE)
    if addon is None:
        return None

    return addon.preferences


def normalize_dir_path(path: str) -> str:
    if not path:
        return ""
    path = bpy.path.abspath(path)
    return os.path.normpath(path)


def get_selected_osc_folder(context=None) -> str:
    prefs = get_addon_preferences(context)
    if prefs is None:
        return ""
    return normalize_dir_path(prefs.reaper_osc_folder)


def get_packaged_reaper_osc_path() -> str:
    return os.path.join(os.path.dirname(__file__), "resources", REAPER_OSC_FILENAME)


def get_installed_reaper_osc_path(context=None) -> str:
    folder = get_selected_osc_folder(context)
    if not folder:
        return ""
    return os.path.join(folder, REAPER_OSC_FILENAME)