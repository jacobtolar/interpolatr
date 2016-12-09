# Copyright 2017, Yahoo Inc.
# Licensed under the terms of the Apache License, Version 2.0.
# See the LICENSE file associated with the project for terms.

"""
Utility functions for interpolatr
"""

import interpolatr
import importlib
import click
import logging


def setup_logging(debug, log_file):
    """
    Set up logging - info or debug to console and debug to a file
    """
    fmt = '%(asctime)s - %(name)s - %(levelname)8s: %(message)s'
    level = logging.DEBUG if debug else logging.INFO

    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.NOTSET)

    streamhandler = logging.StreamHandler()
    streamhandler.setLevel(level)
    streamhandler.setFormatter(logging.Formatter(fmt))
    rootLogger.addHandler(streamhandler)

    if log_file:
        filehandler = logging.FileHandler(log_file)
        filehandler.setLevel(logging.NOTSET)
        filehandler.setFormatter(logging.Formatter(fmt))
        rootLogger.addHandler(filehandler)

import_cache = {
    'interpolatr': interpolatr
}


def lookup_import(name):
    """
    Given a name, try to find it as an interpolatr builtin, than as a module
    import.

    :param name: qualified class name
    """
    if hasattr(import_cache['interpolatr'], name):
        return getattr(import_cache['interpolatr'], name)

    dotted = name.split('.')
    classname = dotted[-1]

    if len(dotted) == 1:
        raise Exception('Module import required; specified: {0}'.format(name))
    else:
        module = '.'.join(dotted[0:-1])

    if module not in import_cache:
        import_cache[module] = importlib.import_module(module)

    return getattr(import_cache[module], classname)


class InterpolatrCommand(click.MultiCommand):
    """
    Command-line class that allows dynamic lookup of commands.
    """
    def get_command(self, ctx, name):
        """
        Given a command name, build the command.

        :param ctx: click context.
        :param name: command name
        """
        cls = lookup_import(name)
        args = cls.get_args()

        @click.pass_context
        def callback(ctx, *args, **kwargs):
            return cls.create(*args, **kwargs)

        return click.Command(name, params=args, callback=callback)

    def format_usage(self, ctx, formatter):
        """
        Usage for the interpolatr command.

        Overrides the default usage to make the expected usage more clear:
        the command should specify a conf or provider class.
        """
        pieces = [
            '[OPTIONS]',
            '[<conf-class> [ARGS]...]...',
            '[<supplier-class> [ARGS]...]...'
        ]

        formatter.write_usage(ctx.command_path, ' '.join(pieces))
