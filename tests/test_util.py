import interpolatr.util

def test_import_lookup():
    """
    We should be able to look up an import by class and instantiate it
    """
    cls = interpolatr.util.lookup_import('interpolatr.config.YamlConfigSource')
    assert cls.__name__ == 'YamlConfigSource'
