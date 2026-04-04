# deps.py

import importlib.util

PYTHONOSC_MODULE = "pythonosc"


def has_pythonosc():
    try:
        return importlib.util.find_spec(PYTHONOSC_MODULE) is not None
    except Exception:
        return False


def get_missing_dependencies():
    missing = []

    if not has_pythonosc():
        missing.append("python-osc")

    return missing


def dependencies_ok():
    return len(get_missing_dependencies()) == 0


def get_dependency_error_message():
    missing = get_missing_dependencies()
    if not missing:
        return ""
    return "Some dependencies missing. Check the installation manual."