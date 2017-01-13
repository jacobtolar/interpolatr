# Copyright 2017, Yahoo Inc.
# Licensed under the terms of the Apache License, Version 2.0.
# See the LICENSE file associated with the project for terms.

"""
Built-in configuration sinks for interpolatr
"""

from contextlib import closing
import click
import os
import logging
import re
from collections import Iterator

from jinja2 import Environment, FileSystemLoader, contextfunction

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

TOKEN_PAT = re.compile('^\$\((.*)\)$')


def replace_regex_jinja(inp, find, replace):
    """ Jinja regex replace function """
    return re.sub(find, replace, inp)


@contextfunction
def default_finalize(ctx, thing):
    """
    Default finalizer used for interpolation with Jinja.

    Does two things:
        - coalesce false-y values to ''
        - A hacky 1-level lookup back into the context if we get something
          that looks like a key. (Assumes keys look like $(...).
    """
    if thing is None:
        return ''

    m = TOKEN_PAT.match(str(thing))
    if m:
        nested = ctx.get(m.group(1))
        return nested if nested is not None else ''
    else:
        return thing


# You could override this if you want,
# but it does defaults nice things for you
def build_default_env(loader, filters=None, **kwargs):
    """
    Build jinja environment with default finalizer and some other defaults.

    :param loader: jinja loader
    :keyword filters: filters to use

    Other parameters in kwargs will be passed directly to the environment.
    """
    kwargs['loader'] = loader

    filters = filters or {'replace_regex': replace_regex_jinja}

    # Defaults
    if 'variable_start_string' not in kwargs:
        kwargs['variable_start_string'] = '$('

    if 'variable_end_string' not in kwargs:
        kwargs['variable_end_string'] = ')'

    if 'finalize' not in kwargs:
        kwargs['finalize'] = default_finalize

    env = Environment(
        **kwargs
    )

    env.filters.update(filters)

    return env


class BaseTemplate(object):
    """
    Source of jinja2 templates. Renders self (returns a generator for chunks
    of rendered content) via the `interpolate` method.

    Templates take a `sink` via the constructor. The sink should be a `Sink`
    object (see below). The `commit` method interpolates the template
    using the provided jinja2 context and writes the resulting chunks to the
    sink.
    """

    # subclass should call super() in constructor
    def __init__(self, sink):
        self.sink = sink

    def interpolate(self, context):
        """
        Interpolate template given context.

        :param context: dict-like object
        """
        t = self.get_template()
        return t.generate(context)

    def get_template(self):
        """
        Return a jinja2 template object.
        """
        raise NotImplementedError('Not implemented!')

    def commit(self, context):
        """
        Commit the interpolated template to somewhere.

        :param context: dict-like object
        """

        # Open the sink object for writing
        self.sink.open()

        with closing(self.sink):
            for chunk in self.interpolate(context):
                self.sink.write(chunk)


class FileTemplate(BaseTemplate):
    """
    A file template source.
    """
    def __init__(self, sink, env, path):
        super(FileTemplate, self).__init__(sink)

        self.env = env
        self.path = path

    def get_template(self):
        return self.env.get_template(self.path)


class Sink(object):
    """
    A sink should render a template given a context, and must `commit` it
    (presumably, to some persistent store such as a file).
    """
    def open(self):
        """
        Open the sink for writing. May be a no-op.
        """
        pass

    def close(self):
        """
        Close the sink. May be a no-op.
        """
        pass

    def write(self, chunk):
        """
        Write a chunk of interpolated data to the sink. Must be implemented.

        :param chunk: chunk of content to write
        """
        raise NotImplementedError('Not implemented!')


class FileSink(Sink):
    """
    A file sink can render templates to the given file.
    """
    def __init__(self, outpath):
        self.outpath = outpath
        self.fh = None

    def open(self):
        self.fh = open(self.outpath, 'w')

    def close(self):
        self.fh.close()
        self.fh = None

    def write(self, chunk):
        self.fh.write(chunk)


class SinkSupplier(Iterator):

    def __init__(self):
        self._iter = None

    # This is silly, but is an artifact of how these are created.
    @classmethod
    def object_type(cls):
        return 'SinkSupplier'

    # python2 wants next()
    def next(self):
        return self.__next__()

    # python3 wants __next__
    def __next__(self):
        if self._iter is None:
            self._iter = self.generate_outputs()
        return next(self._iter)

    def generate_outputs(self):
        """
        Generator to create template objects. Typical usage would be to treat
        the supplier as an iterator, commit()ing each object returned.
        """
        raise NotImplementedError('Not implemented!')


class ExtensionFileSinkSupplier(SinkSupplier):
    """
    Generator for FileSinks using an extension to find files
    """

    def __init__(self, path, extension='.interpolate', recursive=True):
        """
        Create extension sink supplier

        :param path: base template search path
        :keyword extension: extension to search for (default .interpolate)
        :keyword recursive: search recursively (default true)
        """
        super(ExtensionFileSinkSupplier, self).__init__()
        self.path = path
        self.extension = extension
        self.recursive = recursive
        self.env = build_default_env(
            FileSystemLoader(path)
        )

    def generate_outputs(self):
        for root, dirs, files in os.walk(self.path):
            plain_files = (f for f in files if os.path.isfile(
                os.path.join(root, f)))
            for filename in plain_files:
                fpath = os.path.join(root, filename)

                if os.path.isfile(fpath) and fpath.endswith(self.extension):
                    output_file = os.path.splitext(fpath)[0]
                    template_path = os.path.relpath(fpath, self.path)
                    yield FileTemplate(
                        FileSink(output_file),
                        self.env,
                        template_path
                    )
            if not self.recursive:
                break

    @classmethod
    def create(cls, target_dir=None, extension='.interpolate', recursive=True):
        # Normalize the target directory
        target_dir = os.path.abspath(target_dir)
        if not os.path.exists(target_dir):
            raise Exception('target_dir {0} does not exist'.format(target_dir))

        return cls(target_dir, extension, recursive)

    @classmethod
    def get_args(cls):
        """
        Return the array of arguments to click. For use if specified
        on the command line.
        """
        return [
            click.Option(('--recursive/--no-recursive',),
                         help='Recurse into search dir.', default=True),
            click.Option(('--extension',),
                         help='Extension of files to search for.',
                         default='.interpolate'),
            click.Option(('--target_dir',), '-t', help='Search directory.',
                         default=os.getcwd())
        ]
