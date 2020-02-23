from argser.docstring import _normalize_docstring, parse_sphinx_docstring


class TestNormaliseDocstring:
    def test_short(self):
        res = _normalize_docstring("""foo""")
        assert res == 'foo'

    def test_first_line_start(self):
        res = _normalize_docstring(
            """foo
            bar
                baz
            """
        )
        assert res == 'foo\nbar\n    baz'

    def test_second_line_start(self):
        res = _normalize_docstring(
            """
            foo
            bar
                baz
            """
        )
        assert res == 'foo\nbar\n    baz'


class TestSphinxDocstring:
    def test_simple(self):
        res = parse_sphinx_docstring("foo bar\n:param baz: description")
        assert res['description'] == 'foo bar'
        assert res['params']['baz'] == 'description'

    def test_multiline_desc(self):
        res = parse_sphinx_docstring("foo bar\n\nbaz  \naaaa\n:param baz: description")
        assert res['description'] == 'foo bar\n\nbaz  \naaaa'
        assert res['params']['baz'] == 'description'

    def test_multiple_params(self):
        res = parse_sphinx_docstring("foo\n:param p1: d1\n:param p2: d2\n")
        assert res['description'] == 'foo'
        assert res['params']['p1'] == 'd1'
        assert res['params']['p2'] == 'd2'

    def test_multiline_params(self):
        res = parse_sphinx_docstring("foo\n:param p1: d1\n    c1 d1\n   c2 d1\n:param p2: d2\n")
        assert res['description'] == 'foo'
        assert res['params']['p1'] == 'd1 c1 d1 c2 d1'
        assert res['params']['p2'] == 'd2'

    def test_multiline_params_no_indent(self):
        res = parse_sphinx_docstring("foo\n:param p1: d1\nc1 d1\n:param p2: d2\n")
        assert res['description'] == 'foo'
        assert res['params']['p1'] == 'd1'
        assert res['params']['p2'] == 'd2'

    def test_multiline_params_break(self):
        res = parse_sphinx_docstring("foo\n:param p1: d1\n  c1 d1\n\n  c2 d1\n:param p2: d2\n")
        assert res['description'] == 'foo'
        assert res['params']['p1'] == 'd1 c1 d1'  # no c2 here because of extra new line
        assert res['params']['p2'] == 'd2'
