import os
from tempfile import mkstemp
from contextlib import closing

def test_regex_replace():
    from interpolatr.sink import replace_regex_jinja

    assert replace_regex_jinja('http://yahoo.com', '[^/]*//', '') == \
        'yahoo.com'

def test_default_finalize():
    from interpolatr.sink import default_finalize

    context = {
        'something': 'else'
    }

    # None => empty string
    assert default_finalize(context, None) == ''

    # Normal things are just passed through
    assert default_finalize(context, 'foo') == 'foo'

    # 1 level of recursive lookup is done, but no more...
    assert default_finalize(context, '$(something)') == 'else'

    # Missing variable should just resolve to empty string.
    assert default_finalize(context, '$(whatever)') == ''

def test_file_template():
    from interpolatr.sink import FileTemplate, build_default_env, Sink
    from jinja2 import FileSystemLoader
    class DummySink(Sink):
        def __init__(self):
            self.content = ''
        def write(self, chunk):
            self.content += chunk

    sink = DummySink()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(dir_path, 'resources')
    env = build_default_env(FileSystemLoader(path))

    template = FileTemplate(sink, env, 'interp.txt')
    template.commit({'foo_setting': 'one', 'bar_setting': '2'})

    assert sink.content == "one and 2"

def test_file_sink():
    from interpolatr.sink import FileSink
    fh, path = mkstemp()
    os.close(fh)

    sink = FileSink(path)
    sink.open()
    with closing(sink):
        sink.write('123')
        sink.write('456')
    with open(path) as fh:
        assert fh.read() == '123456'

    os.remove(path)

def test_builtin_sink_supplier():
    from interpolatr.sink import ExtensionFileSinkSupplier

    options = ExtensionFileSinkSupplier.get_args()

    # Default extension should be '.interpolate'.
    ext_option = [i for i in options if i.name == 'extension'][0]
    assert ext_option.default == '.interpolate'


    dir_path = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(dir_path, 'resources')
    supplier = ExtensionFileSinkSupplier.create(target_dir=path)

    outputs = [t for t in supplier]
    assert len(outputs) == 1
    outputs[0].commit({'var1': 'val1'})
    try:
        with open(os.path.join(path, 'example')) as f:
            assert f.read() == 'val1 was interpolated!'
    finally:
        os.remove(os.path.join(path, 'example'))

