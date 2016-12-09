# Copyright 2017, Yahoo Inc.
# Licensed under the terms of the Apache License, Version 2.0.
# See the LICENSE file associated with the project for terms.

"""
Built-in configuration sources.

Some, like DictConfigSource or ChainedConfigSource, are mostly just
wrappers around existing python types.

Others, like the YamlConfigSource, are a little more interesting.
"""

import collections
import logging
import os
import re

import click
import yaml

from .compat import ChainMap
from .compat import string_type


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

TOKEN_PAT = re.compile('^\$\((.*)\)$')


class ConfigSourceBase(collections.Mapping):
    """
    A configuration source isn't much more than a mapping.

    It is used as the context passed to your template.

    `ConfigSourceBase` is abstract.

    To be callable from built-in command line tool, your class must implement
    two class methods:
        - get_args: return a list of parameters for click
        - create: create a ConfigSourceBase. create() should accept the
          arguments specified by get_args(). Note that a class method is used
          instead of __new__ because you may want to return a different object
          and doing that from __new__ just confuses people.
    """

    # This is silly, but is necessary for creating these things via the CLI
    @classmethod
    def object_type(cls):
        return 'ConfigSource'

    def dump(self):
        """
        Get a one-per-line view of the map.
        """
        return '\n'.join('{0}={1}'.format(k, self[k]) for k in sorted(
            self.keys())
        )

    def classy_dump(self):
        """
        Get a compactly-formatted view of the map contents, including
        the class name. Is used as the default implementation of __repr__().
        """
        return '{0}({1})'.format(
            self.__class__.__name__,
            ','.join('{0}={1}'.format(k, self[k]) for k in sorted(self.keys()))
        )

    def __repr__(self):
        return self.classy_dump()


class DictConfigSource(ConfigSourceBase):
    """
    The simplest config source.

    :param other: dictionary to use a config source
    """
    def __init__(self, other):
        self.other = other

    def __getitem__(self, key): return self.other[key]

    def __len__(self): return len(self.other)

    def __iter__(self): return iter(self.other)


class ChainedConfigSource(ConfigSourceBase, ChainMap):
    """
    A ConfigSource that isa ChainMap.

    Note: this thing used to never throw KeyError (always returned
    None). I've changed this behavior now, but can't remember the reason for
    the original version...
    """
    def __init__(self, *args):
        super(ChainedConfigSource, self).__init__(*args)

    def chain(self, mapping):
        """
        Append a mapping to the end of the chain.
        """
        self.maps.append(mapping)

    def __repr__(self):
        return '{0}({1})'.format(
            self.__class__.__name__,
            ','.join(str(i) for i in self.maps)
        )

    def __str__(self):
        return '{0}(\n    {1}\n)'.format(
            self.__class__.__name__,
            ',\n    '.join(str(i) for i in self.maps)
        )


class YamlConfigSource(ConfigSourceBase):
    """
    Configuration from special YAML file format.
    """

    def __init__(self, path=None):
        if not os.path.isfile(path):
            raise Exception("Could not find file {0}".format(path))

        # FIXME: Not clear -- should these paths be relative to this file,
        # or to the cwd?
        self.abspath = os.path.abspath(path)
        self.dirpath = os.path.dirname(self.abspath)

        conf = None
        with open(self.abspath) as f:
            conf = yaml.load(f.read())
            if not conf:
                logger.warning(
                    'Configuration file {0} seems to be empty'.format(
                        self.abspath
                    )
                )
                conf = {}

        self.settings = conf.get('settings', {})
        self.base = conf.get('base')

    def get_base(self):
        return self.base

    @classmethod
    def get_args(cls):
        """
        Return the array of arguments to click. For use if specified
        on the command line.
        """
        return [click.Option(("--path",), required=True)]

    @classmethod
    def create(cls, path=None):
        """
        Build a ConfigSource from the given path(s).

        Returns a YamlConfigSource if the given argument is a path and the
        file specified by that path contains no base/parents. Otherwise,
        returns a ChainedConfigSource chaining the conf to its base;
        recursively calls itself if base confs are found.

        This tends to flatten the result out a bit (removes layers of
        ChainedConfigSource), as opposed to always returning a
        ChainedConfigSource.

        FIXME: Probably errors badly if you have a cycle in your config
        (a -> b -> a). Don't do that, because we don't check for that
        currently.

        :param cls: class
        :param path: config path
        """
        # If empty list or string passed, return an conf
        return cls.load_single(path)

    @classmethod
    def load_single(cls, path):
        """
        Build a config source from a yaml file, chaining it to
        any parents that are found.

        :param cls: class
        :param path: path to yaml file
        """
        if not path:
            return ChainedConfigSource()

        conf = cls(path)
        base_conf = cls.load_base(conf.get_base(), os.path.dirname(path))
        if len(base_conf) > 0:
            return ChainedConfigSource(conf, base_conf)
        else:
            return conf

    @classmethod
    def load_base(cls, base, dirpath):
        """
        Load base configuration.

        :param cls: class
        :param base: iterable of yaml paths, possibly nested
        :param dirpath: os.path.dirname() of the child
        """

        if not base:
            return ChainedConfigSource()
        elif isinstance(base, string_type):
            return cls.load_single(os.path.join(dirpath, base))

        # If a list of things is passed, it's an optionally-nested list of
        # paths. Chain all their confs together.
        # Note: Allowing this syntax complicates things and is annoying.
        elif isinstance(base, collections.Iterable):
            confs = [cls.load_base(b, dirpath) for b in base]
            if len(confs) == 1:
                return confs[0]
            else:
                return ChainedConfigSource(*confs)
        else:
            raise Exception('error: {}', base)

    def __getitem__(self, key):
        return self.settings[key]

    def __len__(self):
        return len(self.settings)

    def __iter__(self):
        return iter(self.settings)

    def __repr__(self):
        return 'YamlConfigSource({0})'.format(self.abspath)


class CliConfigSource(ConfigSourceBase):
    """
    Configuration from the command line.
    """
    def __init__(self, overrides):
        self._overrides = {}
        for arg in overrides or []:
            k, v = arg.split('=', 1)
            self._overrides[k] = v

    def __iter__(self):
        return iter(self._overrides)

    def __len__(self):
        return len(self._overrides)

    def __getitem__(self, key):
        return self._overrides[key]
