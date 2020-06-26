import eztoml
import unittest

import eztoml.source

src = eztoml.source.Source


class TestDecoder(unittest.TestCase):

    decoder = eztoml.Decoder()

    def assert_str_decode(self, source, expected):
        source = eztoml.source.Source(source)
        decoded = self.decoder._decode_str(source)
        self.assertEqual(decoded, expected)

    def test_escaped_string(self):
        self.assert_str_decode(r'"hello world"', "hello world")
        self.assert_str_decode(r'"hello \r\n world"', "hello \r\n world")

    def test_literal_string(self):
        self.assert_str_decode(r"'hello world'", "hello world")
        self.assert_str_decode(r"'hello\world'", "hello\\world")

    def test_multiline_string(self):
        self.assert_str_decode(
            r'''"""
hello
    world
        """''',
            "hello\n    world\n        ",
        )
        self.assert_str_decode(
            r'''"""
hello \
    world\
        """''',
            "hello world",
        )
