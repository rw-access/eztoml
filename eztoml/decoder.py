from __future__ import unicode_literals

import datetime
import re

from .errors import EzTomlDecodeError
from .source import Source
from .tokens import (
    DQ_MULTI,
    DQ_INLINE,
    SQ_MULTI,
    SQ_INLINE,
    NAN,
    POS_INF,
    NEG_INF,
    RE_FLAGS,
    CONTROL_CHARS,
    ESCAPES,
)
from .tz import EzTomlTz
from .utils import string_types

try:
    from_codepoint = unichr
except NameError:
    from_codepoint = chr


class Decoder(object):

    __escapes = ESCAPES
    _time_regex = re.compile(r"^(\d{2}):(\d{2}):(\d{2})(?:\.(\d{3,}))?")
    _date_regex = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
    _tz_regex = re.compile(r"^(Z|[-+]\d{2}:\d{2})")
    _datetime_regex = re.compile(
        _date_regex.pattern[1:] + r"(?:[T ]" + _time_regex.pattern[1:] + ")" + _tz_regex.pattern[1:] + "?"
    )
    _hex_regex = re.compile(r"^0x[A-Za-z0-9](?:_?[A-Za-z0-9])*")
    _octal_regex = re.compile(r"^0o[0-7](?:_?[0-7])*")
    _int_regex = re.compile(r"^[-+]?[0-9](?:_?[0-9])*")
    _binary_regex = re.compile(r"^0b[0-1](?:_?[0-1])*")
    _float_regex = re.compile(r"^[-+]?[0-9](?:_?[0-9])*(?:\.[0-9](?:_?[0-9])*)?(?:[eE][+-]?[0-9](?:_?[0-9])*)?")
    _key_regex = re.compile(r"^[-_A-Za-z0-9]+", RE_FLAGS)
    _is_hex4 = staticmethod(re.compile(r"^[A-Za-z0-9]{4}").match)
    _is_hex8 = staticmethod(re.compile(r"^[A-Za-z0-9]{8}").match)
    _get_escape = staticmethod(__escapes.get)
    _is_control_char = staticmethod(CONTROL_CHARS.__contains__)

    def decode(self, source):
        if isinstance(source, bytes):
            source = source.decode("utf-8")

        if isinstance(source, string_types):
            source = Source(source)
        elif not isinstance(source, Source):
            raise EzTomlDecodeError("Expected a Source or String to decode")

        source.eat_ws()
        document = self._decode_root(source)
        source.eat_ws()

        if not source.eof:
            raise EzTomlDecodeError("Extraneous input")

        return document

    def _decode_root(self, source):
        document = {}
        source.eat_ws()

        while not source.eof:
            if source.has_prefix("[["):
                self._decode_table_array(source, document)
            elif source.has_prefix("["):
                self._decode_table(source, document, allow_existing=True)
            elif source.peek(1) in (SQ_INLINE, DQ_INLINE) or source.peek_match(self._key_regex):
                self._decode_kv(source, document)
            else:
                raise EzTomlDecodeError("Unknown input")

            source.eat_ws()

        return document

    def _make_table_path(self, path, document, check_arrays=True):
        sub_table = document
        for k in path:
            if k not in sub_table:
                sub_table = sub_table.setdefault(k, {})
                continue

            sub_table = sub_table[k]

            if not isinstance(sub_table, dict):
                if check_arrays and isinstance(sub_table, list) and len(sub_table) > 0:
                    if len(sub_table) > 0 and all(isinstance(t, dict) for t in sub_table):
                        sub_table = sub_table[-1]
                        continue

                raise EzTomlDecodeError("Key path overlaps with existing value")

        return sub_table

    def _decode_kv(self, source, table):
        keys = set()

        while not source.eof and not source.has_prefix("["):
            key = self._decode_key(source)

            # if no key was found, then we're done
            if key == ():
                raise EzTomlDecodeError("Expected a key")

            # can't redefine a key within an already constructed dict/table
            for subkey_len in range(1, len(key)):
                subkey = key[:subkey_len]
                if subkey in keys:
                    raise EzTomlDecodeError(
                        "Can't add key {key} when {subkey} is already defined".format(key=key, subkey=subkey)
                    )

            keys.add(key)

            source.eat_inline_ws()
            if source.take(1) != "=":
                raise EzTomlDecodeError("Missing = after table key")

            source.eat_inline_ws()
            sub_table = self._make_table_path(key[:-1], table)

            if key[-1] in sub_table:
                raise EzTomlDecodeError("Duplicate key {}".format(key))

            value = self._decode_value(source)

            source.eat_ws(must_advance=True)
            sub_table[key[-1]] = value
            keys.add(key)

        return table

    def _decode_table(self, source, document, allow_existing=False):
        if not source.has_prefix("[") or source.has_prefix("[["):
            raise EzTomlDecodeError("Expected table")

        source.take(1)
        source.eat_inline_ws()
        path = self._decode_key(source)
        parent_table = self._make_table_path(path[:-1], document)

        if path[-1] in parent_table:
            existing = parent_table[path[-1]]
            if not isinstance(existing, dict):
                raise EzTomlDecodeError("Value already defined as {}".format(type(existing).__name__.lower()))

            has_kv = any(not isinstance(v, dict) for v in existing.values())
            if allow_existing is False or has_kv:
                raise EzTomlDecodeError("Duplicated table")

        # create a table if it doesn't exist, otherwise take the one that does
        table = parent_table.setdefault(path[-1], {})
        source.eat_inline_ws()

        if source.take(1) != "]":
            raise EzTomlDecodeError("Unclosed table initializer. Expected: ]")

        source.eat_ws(must_advance=True)
        return self._decode_kv(source, table)

    def _decode_table_array(self, source, document):
        if source.take(2) != "[[":
            raise EzTomlDecodeError("Expected table")

        source.eat_inline_ws()
        path = self._decode_key(source)
        parent_table = self._make_table_path(path[:-1], document)
        table = {}

        if isinstance(parent_table.get(path[-1]), list) and len(parent_table[path[-1]]) == 0:
            raise EzTomlDecodeError("Can't add table to existing list")

        if not isinstance(parent_table.setdefault(path[-1], []), list):
            raise EzTomlDecodeError("Duplicated table")

        parent_table[path[-1]].append(table)
        source.eat_inline_ws()

        if source.take(2) != "]]":
            raise EzTomlDecodeError("Unclosed table array initializer. Expected: ]]")

        source.eat_ws(must_advance=True)
        return self._decode_kv(source, table)

    def _decode_key(self, source):  # type: (Source) -> tuple[str]
        path = []

        while not source.eof:
            source.eat_inline_ws()
            char = source.peek(1)
            dotted = char == "."

            if dotted:
                if not path:
                    raise EzTomlDecodeError("Unexpected dotted key")

                source.take(1)
                source.eat_inline_ws()
                char = source.peek(1)

            key_peek = source.peek_match(self._key_regex)

            if key_peek is not None:
                path.append(source.take(len(key_peek)))
            elif char == DQ_INLINE:
                path.append(self._decode_escaped_str(source))
            elif char == SQ_INLINE:
                path.append(self._decode_literal_str(source))
            else:
                if dotted and not path:
                    raise EzTomlDecodeError("Unmatched dot for key")

                return tuple(path)

        raise EzTomlDecodeError("Unexpected EOF while parsing key")

    def _decode_inline_table(self, source):
        if not source.remove_prefix("{"):
            raise EzTomlDecodeError("Expected {")

        source.eat_ws()
        table = {}

        while not source.eof:
            if source.remove_prefix("}"):
                return table

            if table:
                if not source.remove_prefix(","):
                    raise EzTomlDecodeError("Expected , or }")
                source.eat_inline_ws()

            key = self._decode_key(source)
            parent_table = self._make_table_path(key[:-1], table, check_arrays=False)
            if key[-1] in parent_table:
                raise EzTomlDecodeError("Duplicate key for inline table")

            source.eat_inline_ws()
            if not source.remove_prefix("="):
                raise EzTomlDecodeError("Missing = for inline table key")

            source.eat_inline_ws()
            parent_table[key[-1]] = self._decode_value(source)
            source.eat_inline_ws()

        raise EzTomlDecodeError("Expected } not EOF")

    def _decode_inline_array(self, source):
        if source.take(1) != "[":
            raise EzTomlDecodeError("Expected [")

        source.eat_ws()
        array = []

        while not source.eof:
            if array:
                if source.remove_prefix(","):
                    source.eat_ws()
                elif not source.has_prefix("]"):
                    break

            if source.remove_prefix("]"):
                return array

            array.append(self._decode_value(source))
            source.eat_ws()

        raise EzTomlDecodeError("Expected ]")

    def _decode_str(self, source):
        if source.has_prefix(DQ_MULTI):
            return self._decode_escaped_str_multiline(source)
        elif source.has_prefix(SQ_MULTI):
            return self._decode_literal_str_multiline(source)
        elif source.has_prefix(DQ_INLINE):
            return self._decode_escaped_str(source)
        elif source.has_prefix(SQ_INLINE):
            return self._decode_literal_str(source)
        else:
            raise EzTomlDecodeError("Unknown string type")

    @classmethod
    def _unescape(cls, source):
        # \uXXXX     - unicode         (U+XXXX)
        # \UXXXXXXXX - unicode         (U+XXXXXXXX)
        char = source.take(1)
        if char in "uU":
            size = 4 if char == "u" else 8
            match = cls._is_hex4 if char == "u" else cls._is_hex8
            scalar = source.take(size)
            if match(scalar) is None:
                raise EzTomlDecodeError("Expected a valid unicode scalar value")

            try:
                return from_codepoint(int(scalar, 16))
            except ValueError:
                raise EzTomlDecodeError("Invalid unicode scalar value")

        else:
            unescaped = cls._get_escape(char)
            if unescaped is None:
                raise EzTomlDecodeError("Unknown escape sequence")
            return unescaped

    def _decode_escaped_str_multiline(self, source):  # type: (Source) -> str
        # Basic strings are surrounded by quotation marks.
        if source.take(3) != DQ_MULTI:
            raise EzTomlDecodeError("Expected {}".format(DQ_MULTI))

        source.remove_prefix("\n") or source.remove_prefix("\r\n")
        pieces = []

        while not source.eof:
            if source.has_prefix(DQ_MULTI):
                source.take(3)

                # strings ending with """" -> "
                if source.has_prefix(DQ_INLINE):
                    pieces.append(source.take(1))

                # strings ending with """"" -> ""
                if source.has_prefix(DQ_INLINE):
                    pieces.append(source.take(1))

                return "".join(pieces)

            char = source.take(1)

            if char == "\\":
                if source.has_prefix("\n") or source.peek(2) == "\r\n":
                    # When the last non-whitespace character on a line is an unescaped \,
                    # it will be trimmed along with all whitespace (including newlines)
                    # up to the next non-whitespace character or closing delimiter.
                    source.eat_ws()
                    continue

                pieces.append(self._unescape(source))
            elif char not in "\r\t\n" and self._is_control_char(char):
                raise EzTomlDecodeError("Invalid use of unescaped control character")
            else:
                pieces.append(char)

        raise EzTomlDecodeError("Unexpected EOF while waiting for {}".format(DQ_MULTI))

    def _decode_literal_str_multiline(self, source):
        if source.take(3) != SQ_MULTI:
            raise EzTomlDecodeError("Expected {}".format(SQ_MULTI))

        source.remove_prefix("\n") or source.remove_prefix("\r\n")
        pieces = []

        while not source.eof:
            if source.has_prefix(SQ_MULTI):
                source.take(3)

                # strings ending with '''' -> '
                if source.peek(1) == SQ_INLINE:
                    pieces.append(source.take(1))

                # strings ending with ''''' -> ''
                if source.peek(1) == SQ_INLINE:
                    pieces.append(source.take(1))

                return "".join(pieces)

            char = source.take(1)

            if char not in "\r\t\n" and self._is_control_char(char):
                raise EzTomlDecodeError("Invalid use of unescaped control character")
            else:
                pieces.append(char)

        raise EzTomlDecodeError("Unexpected EOF while waiting for {}".format(SQ_MULTI))

    def _decode_escaped_str(self, source):
        if source.take(1) != DQ_INLINE:
            raise EzTomlDecodeError("Expected {}".format(DQ_INLINE))

        pieces = []

        while not source.eof:
            if source.peek(1) == DQ_INLINE:
                source.take(1)
                return "".join(pieces)

            char = source.take(1)

            if char in "\r\n":
                raise EzTomlDecodeError("Unexpected EOL while parsing newline character")
            elif char == "\\":
                pieces.append(self._unescape(source))
            elif self._is_control_char(char):
                raise EzTomlDecodeError("Invalid use of unescaped control character")
            else:
                pieces.append(char)

        raise EzTomlDecodeError("Unexpected EOF while waiting for {}".format(DQ_INLINE))

    def _decode_literal_str(self, source):
        # Basic strings are surrounded by quotation marks.
        if source.take(1) != SQ_INLINE:
            raise EzTomlDecodeError("Expected {}".format(SQ_INLINE))

        pieces = []

        while not source.eof:
            if source.has_prefix(SQ_INLINE):
                source.take(1)
                return "".join(pieces)

            char = source.take(1)

            if char == "'":
                return "".join(pieces)
            elif char in "\r\n":
                raise EzTomlDecodeError("Unexpected EOL while parsing newline character")
            elif char != "\t" and self._is_control_char(char):
                raise EzTomlDecodeError("Invalid use of unescaped control character")
            else:
                pieces.append(char)

        raise EzTomlDecodeError("Unexpected EOF while waiting for {}".format(SQ_INLINE))

    @staticmethod
    def _to_int(src, base):
        return int(src.replace("_", ""), base)

    def _decode_number(self, source):  # type: (Source) -> int|float
        try:
            if source.has_prefix("0x"):
                return self._to_int(source.take_match(self._hex_regex), 16)
            elif source.has_prefix("0o"):
                return self._to_int(source.take_match(self._octal_regex), 8)
            elif source.has_prefix("0b"):
                return self._to_int(source.take_match(self._binary_regex), 2)
            else:
                int_match = source.peek_match(self._int_regex)
                float_match = source.peek_match(self._float_regex)

                assert int_match is not None

                # check for duplicate leading zeros
                leading = int_match.lstrip("-+").split(".")[0]
                if leading != "0" and leading.startswith("0"):
                    raise EzTomlDecodeError("Invalid leading zeros")

                assert float_match is not None and int_match is not None

                if float_match == int_match:
                    return self._to_int(source.take(len(int_match)), 10)
                else:
                    return float(source.take(len(float_match)).replace("_", ""))

        except AssertionError as exc:
            raise EzTomlDecodeError("Did not find a valid number")

    def _decode_value(self, source):
        check_time = source.peek_match(self._time_regex)
        check_date = source.peek_match(self._date_regex)
        check_datetime = source.peek_match(self._datetime_regex)

        if check_time:
            source.take(len(check_time))
            groups = list(filter(None, self._time_regex.match(check_time).groups()))

            # pad and truncate to microsecond precision
            if len(groups) == 4:
                groups[-1] = groups[-1].ljust(6, "0")[:6]

            try:
                return datetime.time(*[int(g) for g in groups])
            except ValueError:
                raise EzTomlDecodeError("Invalid RFC-3399 time")
        elif check_datetime:
            source.take(len(check_datetime))
            groups = list(self._datetime_regex.match(check_datetime).groups())
            tz_string = groups.pop()
            tz_info = EzTomlTz(tz_string) if tz_string else None

            groups = list(filter(None, groups))

            # pad and truncate to microsecond precision
            if len(groups) == 7:
                groups[-1] = groups[-1].ljust(6, "0")[:6]

            try:
                return datetime.datetime(*[int(g) for g in groups], tzinfo=tz_info)
            except ValueError:
                raise EzTomlDecodeError("Invalid RFC-3399 time")
        elif check_date:
            source.take(len(check_date))
            groups = list(self._date_regex.match(check_date).groups())

            try:
                return datetime.date(*[int(g) for g in groups])
            except ValueError:
                raise EzTomlDecodeError("Invalid RFC-3399 time")
        elif source.has_prefix("{"):
            return self._decode_inline_table(source)
        elif source.has_prefix("["):
            return self._decode_inline_array(source)
        elif source.peek(1) in "'\"":
            return self._decode_str(source)
        elif source.remove_prefix("true"):
            return True
        elif source.remove_prefix("false"):
            return False
        elif source.remove_prefix("+nan") or source.remove_prefix("-nan") or source.remove_prefix("nan"):
            return NAN
        elif source.remove_prefix("+inf") or source.remove_prefix("inf"):
            return POS_INF
        elif source.remove_prefix("-inf"):
            return NEG_INF
        elif source.peek(1) in "+-" or source.peek(1).isdigit():
            return self._decode_number(source)
        else:
            raise EzTomlDecodeError("Missing value")
