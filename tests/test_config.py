import os


def test_dict_config():
    from interpolatr.config import DictConfigSource

    conf = DictConfigSource({'1': '2', 'three': 'four'})
    assert conf.get('1') == '2'
    assert conf.get('three') == 'four'
    assert conf.get('five') == None

    # exercise __len__
    assert len(conf) == 2

    # exercise __iter__
    assert len([i for i in conf]) == 2

    # Test stringifying methods
    assert conf.dump() == '1=2\nthree=four'
    assert conf.classy_dump() == 'DictConfigSource(1=2,three=four)'
    assert repr(conf) == 'DictConfigSource(1=2,three=four)'


def test_cli_config():
    from interpolatr.config import CliConfigSource

    conf = CliConfigSource(['foo=bar', 'test2=value'])

    assert conf.get('foo') == 'bar'
    assert conf.get('test2') == 'value'
    assert conf.get('other') == None

    # exercise __len__
    assert len(conf) == 2

    # exercise __iter__
    assert len([i for i in conf]) == 2


def test_yaml_config():
    from interpolatr.config import YamlConfigSource

    dir_path = os.path.dirname(os.path.realpath(__file__))
    conf_path = os.path.join(dir_path, 'resources/conf.yaml')

    conf = YamlConfigSource.create(conf_path)

    # overrides base
    assert conf['sample_setting'] == 'child_value'

    # only in child
    assert conf['other_setting'] == 'other_setting'

    # only in base
    assert conf['some_base_setting'] == 'some_value'

    # length should be 3, not 4
    assert len(conf) == 3


def test_chained_config():
    from interpolatr.config import ChainedConfigSource

    conf = ChainedConfigSource()

    d = {'foo': 'bar'}
    conf.chain(d)
    assert conf['foo'] == 'bar'

    d2 = {'foo': 'bar2', 'base': 'only_base'}
    conf.chain(d2)
    assert conf['foo'] == 'bar'
    assert conf['base'] == 'only_base'

    assert len(conf) == 2
