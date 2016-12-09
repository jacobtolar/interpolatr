# Copyright 2017, Yahoo Inc.
# Licensed under the terms of the Apache License, Version 2.0.
# See the LICENSE file associated with the project for terms.

try:
    from collections import ChainMap
except:
    # py2 has extra dependency
    from chainmap import ChainMap

try:
    string_type = basestring
except NameError:
    string_type = str
