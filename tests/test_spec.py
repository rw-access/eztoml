# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import math
import unittest
from datetime import date, datetime, time

from eztoml import loads, EzTomlDecodeError, EzTomlTz, dumps


class TestSpecification(unittest.TestCase):
    def decodes_to(self, text, doc, dump_kwargs=None, load_kwargs=None):
        dump_kwargs = dump_kwargs or {}
        load_kwargs = load_kwargs or {}
        decoded = loads(text, **load_kwargs)
        encoded = dumps(doc, **dump_kwargs)
        self.assertDictEqual(decoded, doc)

        # now, decode the encoded text
        double_decoded = loads(encoded, **load_kwargs)
        self.assertDictEqual(double_decoded, doc)

        return decoded

    def decode_failure(self, text, message=None):
        with self.assertRaises(EzTomlDecodeError) as exc:
            loads(text)

        if message:
            self.assertTrue(str(exc.exception).startswith(message))

    def test_kv(self):
        self.decodes_to('key = "value"', {"key": "value"})
        self.decode_failure('first = "Tom" last = "Preston-Werner" # INVALID)')
        self.decodes_to(
            """
        key = "value"
        bare_key = "value"
        bare-key = "value"
        1234 = "value"
        """,
            {"key": "value", "bare_key": "value", "bare-key": "value", "1234": "value",},
        )

        self.decodes_to(
            """
        "127.0.0.1" = "value"
        "character encoding" = "value"
        "ʎǝʞ" = "value"
        'key2' = "value"
        'quoted "value"' = "value"
        """,
            {
                "127.0.0.1": "value",
                "character encoding": "value",
                "ʎǝʞ": "value",
                "key2": "value",
                'quoted "value"': "value",
            },
        )

    def test_missing_key(self):
        self.decode_failure(
            """
        = "no key name"  # INVALID
        """
        )

    def test_str_key(self):
        self.decodes_to(
            """
        "" = "blank"     # VALID but discouraged
        """,
            {"": "blank"},
        )

        self.decodes_to(
            """
        '' = 'blank'     # VALID but discouraged
        """,
            {"": "blank"},
        )

    def test_dotted_key(self):
        self.decodes_to(
            """
        name = "Orange"
        physical.color = "orange"
        physical.shape = "round"
        site."google.com" = true
        """,
            {"name": "Orange", "physical": {"color": "orange", "shape": "round"}, "site": {"google.com": True},},
        )

        self.decodes_to(
            """
        # Whitespace around dot-separated parts is ignored,
        # however, best practice is to not use any extraneous whitespace.
        a. b = "test"
        x . y . z = "test"
        """,
            {"a": {"b": "test"}, "x": {"y": {"z": "test"}}},
        )

    def test_duplicate_keys(self):
        self.decode_failure(
            """
        # Defining a key multiple times is invalid.

        # DO NOT DO THIS
        name = "Tom"
        name = "Pradyun"
        """
        )

    def test_dotted_numeric_keys(self):
        self.decodes_to(
            """
        3.14159 = "pi"
        """,
            {"3": {"14159": "pi"}},
        )

    def test_dotted_unordered(self):
        self.decodes_to(
            """
        # As long as a key hasn't been directly defined,
        # you may still write to it and to names within it.

        # This makes the key "fruit" into a table.
        fruit.apple.smooth = true
        
        # So then you can add to the table "fruit" like so:
        fruit.orange = 2
        """,
            {"fruit": {"apple": {"smooth": True}, "orange": 2}},
        )

        self.decode_failure(
            """
        # THE FOLLOWING IS INVALID

        # This defines the value of fruit.apple to be an integer.
        fruit.apple = 1
        
        # But then this treats fruit.apple like it's a table.
        # You can't turn an integer into a table.
        fruit.apple.smooth = true
        """
        )

        self.decodes_to(
            """
        # VALID BUT DISCOURAGED
        
        apple.type = "fruit"
        orange.type = "fruit"
        
        apple.skin = "thin"
        orange.skin = "thick"
        
        apple.color = "red"
        orange.color = "orange"
        """,
            {
                "apple": {"type": "fruit", "skin": "thin", "color": "red"},
                "orange": {"type": "fruit", "skin": "thick", "color": "orange"},
            },
        )

        self.decodes_to(
            r"""
        str = "I'm a string. \"You can quote me\". Name\tJos\u00E9\nLocation\tSF."
        """,
            {"str": 'I\'m a string. "You can quote me". Name\tJos\u00E9\nLocation\tSF.'},
        )

    def test_escapes(self):
        self.decodes_to(
            r"""
        backspace = "\b"
        tab = "\t"
        linefeed = "\n"
        formfeed = "\f"
        carriagereturn = "\r"
        quote = "\""
        backslash = "\\"
        unicode4 = "\u1234"
        unicode8 = "\U00012345"
        allofthem = "\b\t\n\f\r\"\\\u1234\U00012345"
        """,
            {
                "backspace": "\b",
                "tab": "\t",
                "linefeed": "\n",
                "formfeed": "\f",
                "carriagereturn": "\r",
                "quote": '"',
                "backslash": "\\",
                "unicode4": "\u1234",
                "unicode8": "\U00012345",
                "allofthem": '\b\t\n\f\r"\\\u1234\U00012345',
            },
            dump_kwargs={"preserve_cr": True},
        )

    def test_escaped_multiline(self):
        self.decodes_to(
            r'''
str1 = """
Roses are red
Violets are blue"""
        ''',
            {"str1": "Roses are red\nViolets are blue"},
        )

        sentence = "The quick brown fox jumps over the lazy dog."
        self.decodes_to(
            r'''
# The following strings are byte-for-byte equivalent:
str1 = "The quick brown fox jumps over the lazy dog."

str2 = """
The quick brown \


  fox jumps over \
    the lazy dog."""

str3 = """\
       The quick brown \
       fox jumps over \
       the lazy dog.\
       """
        ''',
            {"str1": sentence, "str2": sentence, "str3": sentence},
        )

        # test again, but indented
        self.decodes_to(
            r'''
        # The following strings are byte-for-byte equivalent:
        str1 = "The quick brown fox jumps over the lazy dog."
    
        str2 = """\
        The quick brown \
    
    
          fox jumps over \
            the lazy dog."""
    
        str3 = """\
               The quick brown \
               fox jumps over \
               the lazy dog.\
               """
            ''',
            {"str1": sentence, "str2": sentence, "str3": sentence},
        )

        self.decodes_to(
            r'''
        str4 = """Here are two quotation marks: "". Simple enough."""
        # str5 = """Here are three quotation marks: """."""  # INVALID
        str5 = """Here are three quotation marks: ""\"."""
        str6 = """Here are fifteen quotation marks: ""\"""\"""\"""\"""\"."""
        
        # "This," she said, "is just a pointless statement."
        str7 = """"This," she said, "is just a pointless statement.""""

        ''',
            {
                "str4": 'Here are two quotation marks: "". Simple enough.',
                "str5": 'Here are three quotation marks: """.',
                "str6": 'Here are fifteen quotation marks: """"""""""""""".',
                "str7": '"This," she said, "is just a pointless statement."',
            },
        )

        self.decode_failure(
            r'''
        str5 = """Here are three quotation marks: """."""  # INVALID
        '''
        )

    def test_literal_inline(self):
        self.decodes_to(
            """
        # What you see is what you get.
        winpath  = 'C:\\Users\\nodejs\\templates'
        winpath2 = '\\\\ServerX\\admin$\\system32\\'
        quoted   = 'Tom "Dubs" Preston-Werner'
        regex    = '<\\i\\c*\\s*>'
        """,
            {
                "winpath": "C:\\Users\\nodejs\\templates",
                "winpath2": "\\\\ServerX\\admin$\\system32\\",
                "quoted": 'Tom "Dubs" Preston-Werner',
                "regex": "<\\i\\c*\\s*>",
            },
        )

    def test_literal_multiline(self):
        self.decodes_to(
            r"""
regex2 = '''I [dw]on't need \d{2} apples'''
lines  = '''
The first newline is
trimmed in raw strings.
   All other whitespace
   is preserved.
'''
        """,
            {
                "regex2": "I [dw]on't need \\d{2} apples",
                "lines": "The first newline is\n"
                "trimmed in raw strings.\n"
                "   All other whitespace\n"
                "   is preserved.\n",
            },
        )

        self.decodes_to(
            """
        quot15 = '''Here are fifteen quotation marks: \"\"\"\"\"\"\"\"\"\"\"\"\"\"\"'''
        
        # apos15 = '''Here are fifteen apostrophes: ''''''''''''''''''  # INVALID
        apos15 = "Here are fifteen apostrophes: '''''''''''''''"
        
        # 'That,' she said, 'is still pointless.'
        str = ''''That,' she said, 'is still pointless.''''
        
        """,
            {
                "quot15": 'Here are fifteen quotation marks: """""""""""""""',
                "apos15": "Here are fifteen apostrophes: '''''''''''''''",
                "str": "'That,' she said, 'is still pointless.'",
            },
        )

        self.decode_failure(
            """
        apos15 = '''Here are fifteen apostrophes: ''''''''''''''''''  # INVALID
        """
        )

    def test_control_chars(self):
        self.decodes_to(
            """
        tab1 = 'hello\tworld'
        tab2 = "hello\tworld"
        """,
            {"tab1": "hello\tworld", "tab2": "hello\tworld"},
        )

        self.decode_failure(
            """
        ff = 'hello\fworld'
        """
        )

        self.decode_failure(
            """
        bs = 'hello\bworld'
        """
        )

        self.decode_failure(
            """
        nl = 'hello\nworld'
        """
        )

        self.decode_failure(
            """
        cr = 'hello\rworld'
        """
        )

    def test_integer(self):
        decoded = self.decodes_to(
            """
        int1 = +99
        int2 = 42
        int3 = 0
        int4 = -17
        """,
            {"int1": 99, "int2": 42, "int3": 0, "int4": -17},
        )

        for value in decoded.values():
            self.assertIsInstance(value, int)

    def test_integer_separator(self):
        decoded = self.decodes_to(
            """
        int5 = 1_000
        int6 = 5_349_221
        int7 = 1_2_3_4_5     # VALID but discouraged
        """,
            {"int5": 1000, "int6": 5349221, "int7": 12345},
        )

        for value in decoded.values():
            self.assertIsInstance(value, int)

    def test_hex(self):
        decoded = self.decodes_to(
            """
        # hexadecimal with prefix `0x`
        hex1 = 0xDEADBEEF
        hex2 = 0xdeadbeef
        hex3 = 0xdead_beef
        """,
            {"hex1": 0xDEADBEEF, "hex2": 0xDEADBEEF, "hex3": 0xDEADBEEF},
        )

        for v in decoded.values():
            self.assertNotIsInstance(v, float)

    def test_octal(self):
        decoded = self.decodes_to(
            """
        # octal with prefix `0o`
        oct1 = 0o01234567
        oct2 = 0o755 # useful for Unix file permissions
        """,
            {"oct1": 0o1234567, "oct2": 0o755},
        )

        for v in decoded.values():
            self.assertNotIsInstance(v, float)

    def test_binary(self):
        decoded = self.decodes_to(
            """
        # binary with prefix `0b`
        bin1 = 0b11010110
        bin2 = 0b1101_0110
        """,
            {"bin1": 0b11010110, "bin2": 0b11010110},
        )

        for v in decoded.values():
            self.assertNotIsInstance(v, float)

    def test_integer_bounds(self):
        max_int = int(2 ** 63 - 1)
        min_int = int(-(2 ** 64))

        decoded = self.decodes_to(
            """
            max_int = {max_int}
            min_int = {min_int}
            """.format(
                max_int=max_int, min_int=min_int
            ),
            {"max_int": max_int, "min_int": min_int},
        )

        for v in decoded.values():
            self.assertNotIsInstance(v, float)

    def test_float(self):
        decoded = self.decodes_to(
            """
        # fractional
        flt1 = +1.0
        flt2 = 3.1415
        flt3 = -0.01
        
        # exponent
        flt4 = 5e+22
        flt5 = 1e06
        flt6 = -2E-2
        
        # both
        flt7 = 6.626e-34
        """,
            {
                "flt1": +1.0,
                "flt2": 3.1415,
                "flt3": -0.01,
                "flt4": 5e22,
                "flt5": 1e06,
                "flt6": -2e-2,
                "flt7": 6.626e-34,
            },
        )

        for v in decoded.values():
            self.assertIsInstance(v, float)

    def test_float_separators(self):
        self.decodes_to(
            """
        flt8 = 224_617.445_991_228
        """,
            {"flt8": 224617.445991228},
        )

    def test_float_zero(self):
        decoded = self.decodes_to("f = 0.0", {"f": 0.0})
        self.assertEqual(str(decoded["f"]), "0.0")

        decoded = self.decodes_to("f = +0.0", {"f": 0.0})
        self.assertEqual(str(decoded["f"]), "0.0")

        decoded = self.decodes_to("f = -0.0", {"f": -0.0})
        self.assertEqual(str(decoded["f"]), "-0.0")

    def test_float_constants(self):
        decoded = loads(
            """
        # infinity
        sf1 = inf  # positive infinity
        sf2 = +inf # positive infinity
        sf3 = -inf # negative infinity
        
        # not a number
        sf4 = nan  # actual sNaN/qNaN encoding is implementation-specific
        sf5 = +nan # same as `nan`
        sf6 = -nan # valid, actual encoding is implementation-specific
        """
        )

        # in python, NaN == NaN will always be false
        self.assertEqual(len(decoded), 6)
        self.assertEqual(decoded["sf1"], float("inf"))
        self.assertEqual(decoded["sf2"], float("+inf"))
        self.assertEqual(decoded["sf3"], float("-inf"))

        self.assertTrue(math.isnan(decoded["sf4"]))
        self.assertTrue(math.isnan(decoded["sf5"]))
        self.assertTrue(math.isnan(decoded["sf6"]))

    def test_boolean(self):
        self.decodes_to(
            """
        bool1 = true
        bool2 = false
        """,
            {"bool1": True, "bool2": False},
        )

    def test_offset_datetime(self):
        decoded = self.decodes_to(
            """
        # RFC-3339
        odt1 = 1979-05-27T07:32:00Z
        odt2 = 1979-05-27T00:32:00-07:00
        odt3 = 1979-05-27T00:32:00.999999-07:00

        # For the sake of readability, you may replace the T delimiter between date and time
        # with a space character (as permitted by RFC 3339 section 5.6).
        odt4 = 1979-05-27 00:32:00.999999-07:00
        """,
            {
                "odt1": datetime(year=1979, month=5, day=27, hour=7, minute=32, second=0, tzinfo=EzTomlTz("Z"),),
                "odt2": datetime(year=1979, month=5, day=27, hour=0, minute=32, second=0, tzinfo=EzTomlTz("-07:00"),),
                "odt3": datetime(
                    year=1979,
                    month=5,
                    day=27,
                    hour=0,
                    minute=32,
                    second=0,
                    microsecond=999999,
                    tzinfo=EzTomlTz("-07:00"),
                ),  # noqa: E501
                "odt4": datetime(
                    year=1979,
                    month=5,
                    day=27,
                    hour=0,
                    minute=32,
                    second=0,
                    microsecond=999999,
                    tzinfo=EzTomlTz("-07:00"),
                ),  # noqa: E501
            },
        )

        converted = {k: v.isoformat() for k, v in decoded.items()}
        self.assertDictEqual(
            converted,
            {
                "odt1": "1979-05-27T07:32:00+00:00",
                "odt2": "1979-05-27T00:32:00-07:00",
                "odt3": "1979-05-27T00:32:00.999999-07:00",
                "odt4": "1979-05-27T00:32:00.999999-07:00",
            },
        )

    def test_time_offset_precision(self):
        zulu = EzTomlTz("Z")
        self.decode_failure("needs_ms = 1979-05-27T07:32:00.9Z")
        self.decode_failure("needs_ms = 1979-05-27T07:32:00.99Z")
        self.decodes_to(
            """
        prec3 = 1979-05-27T07:32:00.999Z
        prec4 = 1979-05-27T07:32:00.9999Z
        prec5 = 1979-05-27T07:32:00.99999Z
        prec6 = 1979-05-27T07:32:00.999999Z
        
        # more than microseconds will truncate
        # this is implementation defined in TOML, so we'll limit to Python's datetime
        prec7 = 1979-05-27T07:32:00.9999999Z
        prec8 = 1979-05-27T07:32:00.99999999Z
        """,
            {
                "prec3": datetime(
                    year=1979, month=5, day=27, hour=7, minute=32, second=0, microsecond=999000, tzinfo=zulu,
                ),
                "prec4": datetime(
                    year=1979, month=5, day=27, hour=7, minute=32, second=0, microsecond=999900, tzinfo=zulu,
                ),
                "prec5": datetime(
                    year=1979, month=5, day=27, hour=7, minute=32, second=0, microsecond=999990, tzinfo=zulu,
                ),
                "prec6": datetime(
                    year=1979, month=5, day=27, hour=7, minute=32, second=0, microsecond=999999, tzinfo=zulu,
                ),
                "prec7": datetime(
                    year=1979, month=5, day=27, hour=7, minute=32, second=0, microsecond=999999, tzinfo=zulu,
                ),
                "prec8": datetime(
                    year=1979, month=5, day=27, hour=7, minute=32, second=0, microsecond=999999, tzinfo=zulu,
                ),
            },
        )

    def test_local_date_time(self):
        decoded = self.decodes_to(
            """
        ldt1 = 1979-05-27T07:32:00
        ldt2 = 1979-05-27T00:32:00.999999
        """,
            {
                "ldt1": datetime(year=1979, month=5, day=27, hour=7, minute=32, second=0),
                "ldt2": datetime(year=1979, month=5, day=27, hour=0, minute=32, second=0, microsecond=999999,),
            },
        )

        # if there's no timezone, then isoformat won't render one
        converted = {k: v.isoformat() for k, v in decoded.items()}
        self.assertDictEqual(
            converted, {"ldt1": "1979-05-27T07:32:00", "ldt2": "1979-05-27T00:32:00.999999",},
        )

    def test_local_date(self):
        self.decodes_to("ld1 = 1979-05-27", {"ld1": date(year=1979, month=5, day=27)})

    def test_local_time(self):
        self.decodes_to(
            """
        lt1 = 07:32:00
        lt2 = 00:32:00.999999
        """,
            {"lt1": time(hour=7, minute=32, second=0), "lt2": time(hour=0, minute=32, second=0, microsecond=999999),},
        )

    def test_time_precision(self):
        self.decode_failure("prec1 = 00:32:00.9")
        self.decode_failure("prec2 = 00:32:00.99")
        self.decodes_to(
            """
        prec3 = 00:32:00.999
        prec4 = 00:32:00.9999
        prec5 = 00:32:00.99999
        prec6 = 00:32:00.999999
        prec7 = 00:32:00.999999
        prec8 = 00:32:00.999999
        """,
            {
                "prec3": time(hour=0, minute=32, second=0, microsecond=999000),
                "prec4": time(hour=0, minute=32, second=0, microsecond=999900),
                "prec5": time(hour=0, minute=32, second=0, microsecond=999990),
                "prec6": time(hour=0, minute=32, second=0, microsecond=999999),
                "prec7": time(hour=0, minute=32, second=0, microsecond=999999),
                "prec8": time(hour=0, minute=32, second=0, microsecond=999999),
            },
        )

    def test_inline_array(self):
        self.decodes_to(
            """
        integers = [ 1, 2, 3 ]
        colors = [ "red", "yellow", "green" ]
        nested_array_of_int = [ [ 1, 2 ], [3, 4, 5] ]
        nested_mixed_array = [ [ 1, 2 ], ["a", "b", "c"] ]
        string_array = [ "all", 'strings', "\"\"are the same"\"\", '''type''' ]
        
        # Mixed-type arrays are allowed
        numbers = [ 0.1, 0.2, 0.5, 1, 2, 5 ]
        contributors = [
          "Foo Bar <foo@example.com>",
          { name = "Baz Qux", email = "bazqux@example.com", url = "https://example.com/bazqux" }
        ]
        """,
            {
                "integers": [1, 2, 3],
                "colors": ["red", "yellow", "green"],
                "nested_array_of_int": [[1, 2], [3, 4, 5]],
                "nested_mixed_array": [[1, 2], ["a", "b", "c"]],
                "string_array": ["all", "strings", "are the same", "type"],
                "numbers": [0.1, 0.2, 0.5, 1, 2, 5],
                "contributors": [
                    "Foo Bar <foo@example.com>",
                    {"name": "Baz Qux", "email": "bazqux@example.com", "url": "https://example.com/bazqux",},
                ],
            },
        )

    def test_array_multiple_lines(self):
        self.decodes_to(
            """
        integers2 = [
          1, 2, 3
        ]
        """,
            {"integers2": [1, 2, 3]},
        )

    def test_trailing_comma(self):
        self.decodes_to(
            """   
        integers3 = [
          1,
          2, # this is ok
        ]
        """,
            {"integers3": [1, 2]},
        )

    def test_table(self):
        self.decodes_to("[table]", {"table": {}})
        self.decodes_to(
            """
        [table-1]
        key1 = "some string"
        key2 = 123
        
        [table-2]
        key1 = "another string"
        key2 = 456
        """,
            {"table-1": {"key1": "some string", "key2": 123}, "table-2": {"key1": "another string", "key2": 456,},},
        )

    def test_table_string_keys(self):
        self.decodes_to(
            """
        [dog."tater.man"]
        type.name = "pug"
        """,
            {"dog": {"tater.man": {"type": {"name": "pug"}}}},
        )

    def test_table_key_ws(self):
        self.decodes_to(
            """
        [a.b.c]            # this is best practice
        [ d.e.f ]          # same as [d.e.f]
        [ g .  h  . i ]    # same as [g.h.i]
        [ j . "ʞ" . 'l' ]  # same as [j."ʞ".'l']
        """,
            {"a": {"b": {"c": {}}}, "d": {"e": {"f": {}}}, "g": {"h": {"i": {}}}, "j": {"ʞ": {"l": {}}},},
        )

    def test_table_super_order(self):
        self.decodes_to(
            """
        # [x] you
        # [x.y] don't
        # [x.y.z] need these
        [x.y.z.w] # for this to work
        
        [x] # defining a super-table afterward is ok
        
        """,
            {"x": {"y": {"z": {"w": {}}}}},
        )

        self.decodes_to(
            """
        [x.y.z.w]
        deep_hello = "deep world"

        [x]
        hello = "world"
        """,
            {"x": {"y": {"z": {"w": {"deep_hello": "deep world"}}}, "hello": "world"}},
        )

    def test_duplicate_definition(self):
        self.decode_failure(
            """
        [fruit]
        apple = "red"
        
        [fruit]
        orange = "orange"
        """
        )

        self.decode_failure(
            """
        [fruit]
        apple = "red"
        
        [fruit.apple]
        texture = "smooth"
        """
        )

    def test_table_order(self):
        expected = {
            "fruit": {"apple": {}, "orange": {}},
            "animal": {},
        }
        self.decodes_to(
            """
        # VALID BUT DISCOURAGED
        [fruit.apple]
        [animal]
        [fruit.orange]
        """,
            expected,
        )

        self.decodes_to(
            """
        # RECOMMENDED
        [fruit.apple]
        [fruit.orange]
        [animal]
        """,
            expected,
        )

    def test_dotted_keys(self):
        self.decodes_to(
            """
        [fruit]
        apple.color = "red"
        apple.taste.sweet = true

        [fruit.apple.texture]  # you can add sub-tables
        smooth = true
        """,
            {"fruit": {"apple": {"color": "red", "taste": {"sweet": True}, "texture": {"smooth": True},}}},
        )

        self.decode_failure(
            """
        [fruit]
        apple.color = "red"
        apple.taste.sweet = true

        [fruit.apple]  # INVALID
        [fruit.apple.taste]  # INVALID

        [fruit.apple.texture]  # you can add sub-tables
        smooth = true
        """
        )

    def test_inline_tables(self):
        expected = {
            "name": {"first": "Tom", "last": "Preston-Werner"},
            "point": {"x": 1, "y": 2},
            "animal": {"type": {"name": "pug"}},
        }
        self.decodes_to(
            """
        name = { first = "Tom", last = "Preston-Werner" }
        point = { x = 1, y = 2 }
        animal = { type.name = "pug" }
        """,
            expected,
        )

        self.decodes_to(
            """
        [name]
        first = "Tom"
        last = "Preston-Werner"
        
        [point]
        x = 1
        y = 2
        
        [animal]
        type.name = "pug"
        """,
            expected,
        )

        self.decode_failure(
            """
        [product]
        type = { name = "Nail" }
        type.edible = false  # INVALID
        """
        )

        self.decode_failure(
            """
        [product]
        type.name = "Nail"
        type = { edible = false }  # INVALID
        """
        )

    def test_array_of_tables(self):
        self.decodes_to(
            """
        [[products]]
        name = "Hammer"
        sku = 738594937
        
        [[products]]
        
        [[products]]
        name = "Nail"
        sku = 284758393
        
        color = "gray"
        
        """,
            {
                "products": [
                    {"name": "Hammer", "sku": 738594937},
                    {},
                    {"name": "Nail", "sku": 284758393, "color": "gray"},
                ]
            },
        )

        self.decodes_to(
            """
        [[fruit]]
          name = "apple"
        
          [fruit.physical]  # subtable
            color = "red"
            shape = "round"
        
          [[fruit.variety]]  # nested array of tables
            name = "red delicious"
        
          [[fruit.variety]]
            name = "granny smith"
        
        [[fruit]]
          name = "banana"
        
          [[fruit.variety]]
            name = "plantain"
        """,
            {
                "fruit": [
                    {
                        "name": "apple",
                        "physical": {"color": "red", "shape": "round"},
                        "variety": [{"name": "red delicious"}, {"name": "granny smith"},],
                    },
                    {"name": "banana", "variety": [{"name": "plantain"}]},
                ]
            },
        )

    def test_array_of_tables_collision(self):
        self.decode_failure(
            """
        # INVALID TOML DOC
        [fruit.physical]  # subtable, but to which parent element should it belong?
          color = "red"
          shape = "round"
        
        [[fruit]]  # parser must throw an error upon discovering that "fruit" is
                   # an array rather than a table
          name = "apple"
        
        """
        )

        self.decode_failure(
            """
        # INVALID TOML DOC
        fruit = []
        
        [[fruit]] # Not allowed
        """
        )

        self.decode_failure(
            """
        # INVALID TOML DOC
        [[fruit]]
          name = "apple"
        
          [[fruit.variety]]
            name = "red delicious"
        
          # INVALID: This table conflicts with the previous array of tables
          [fruit.variety]
            name = "granny smith"
        
          [fruit.physical]
            color = "red"
            shape = "round"
        
          # INVALID: This array of tables conflicts with the previous table
          [[fruit.physical]]
            color = "green"
        """
        )

    def test_inline_table_points(self):
        self.decodes_to(
            """
        points = [ { x = 1, y = 2, z = 3 },
                   { x = 7, y = 8, z = 9 },
                   { x = 2, y = 4, z = 8 } ]
        """,
            {"points": [{"x": 1, "y": 2, "z": 3}, {"x": 7, "y": 8, "z": 9}, {"x": 2, "y": 4, "z": 8},]},
        )
