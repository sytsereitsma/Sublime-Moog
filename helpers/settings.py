import sublime
import json
import logging


def get(key, default):
    project_settings = sublime.active_window().project_data()
    try:
        value = project_settings["moog"][key]
    except KeyError as e:
        logging.error(e)
        settings = sublime.load_settings("Moog.sublime-settings")
        value = settings.get(key, default)

    return value
