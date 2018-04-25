import sys
import importlib
import core.plugin
import copy

DESCRIPTION = "lists all available modules"

def autocomplete(shell, line, text, state):
    return None

def help(shell):
    pass

def execute(shell, cmd):

    #formats = "\t{0:<32}{1:<32}{2:<32}"
    #shell.print_plain(formats.format("NAME", "AUTHORS", "DESCRIPTION"))
    #shell.print_plain(formats.format("-----", "---------", "-----------"))

    formats = "{0:<42}{1:<64}"
    shell.print_plain(formats.format("NAME", "DESCRIPTION"))
    shell.print_plain(formats.format("----------", "----------------------"))

    keys = shell.plugins.keys()
    keys.sort()

    for key in keys:
        try:
            desc = shell.plugins[key].DESCRIPTION
            auth = shell.plugins[key].AUTHORS
            shell.print_plain(formats.format(key, desc))
        except:
            shell.print_plain(formats.format(key, ""))
            raise
