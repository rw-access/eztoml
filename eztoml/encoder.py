from __future__ import unicode_literals

import re
import unicodedata
from collections import OrderedDict
from contextlib import contextmanager
from datetime import date, time, datetime

from eztoml.errors import EzTomlEncodeError
from .tokens import (
    CONTROL_CHARS,
    SQ_INLINE,
    DQ_INLINE,
    TAB,
    UNESCAPES,
    DQ_MULTI,
    SQ_MULTI,
    NEWLINE,
)
from .utils import string_types, unicode_type, number_types

try:
    from functools import lru_cache
except ImportError:
    # ignore if unavailable
    def lru_cache(**_):
        def decorator(f):
            return f
        return decorator


@lru_cache(maxsize=1024)
def should_unicode_escape(char):
    """Determine if a character needs a unicode escape sequence."""
    if char in " \b\f\n\r\t":
        return False

    category = unicodedata.category(char)
    return category[0] in "CZ"


@lru_cache(maxsize=1024)
def escape_char(char):
    if char in UNESCAPES:
        return UNESCAPES[char]
    elif should_unicode_escape(char):
        codepoint = ord(char)
        if codepoint > 0xFFFF:
            return "\\U{:08x}".format(codepoint)

        return "\\u{:04x}".format(codepoint)
    else:
        return char


def escape(seq):
    return "".join(escape_char(c) for c in seq)


def escape_multi_line(seq):
    return "".join(escape_char(c) if c != '"' else c for c in seq)


class TokenStream(list):
    def __init__(self, nl="\n", indent=2):
        self._nl = nl
        self._prefix = ""
        self.indent = indent
        self.depth = 0
        list.__init__(self)

    def _update_prefix(self):
        self._prefix = self.depth * self.indent * " "
        return self._prefix

    @property
    def is_indented(self):  # type: () -> bool
        return self.depth > 0

    @contextmanager
    def indented(self, depth=None, delta=None):
        assert depth is not None or delta is not None
        new_depth = depth if depth is not None else delta
        depth = self.depth

        try:
            self.depth = new_depth
            self._update_prefix()
            yield self
        finally:
            self.depth = depth
            self._update_prefix()

    def __enter__(self):
        self.depth += 1
        self._update_prefix()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.depth -= 1
        self._update_prefix()

    def appendall(self, *args):
        self.extend(args)

    def flush(self):
        self.append(self._nl)

    def tab(self):
        self.append(self._prefix)

    def __str__(self):
        uc = self.__unicode__()
        if not isinstance(uc, str):
            # py2 compat
            uc = uc.encode("utf-8")
        return uc

    def __unicode__(self):
        return "".join(self)


class Table(object):
    __slots__ = (
        "is_array",
        "path",
        "kv",
        "depth",
    )

    def __init__(self, path, kv, is_array, depth=0):
        # type: (tuple[str], dict, bool, int) -> None
        self.is_array = is_array
        self.path = path
        self.kv = kv
        self.depth = depth

    def __repr__(self):
        return (
            "{self.__class__.__name__}({self.path!r}, {self.kv!r}, "
            "is_array={self.is_array!r}, depth={self.depth!r})".format(self=self)
        )


class Encoder(object):

    _key_regex = re.compile(r"^[-_A-Za-z0-9]+$")
    _word_regex = re.compile(r"[^\s]*\s*", re.MULTILINE | re.DOTALL | re.UNICODE)

    def __init__(self, sort_keys=False, nl="\n", indent=2, wrap=120, preserve_cr=False):
        self.indent = indent
        self.nl = nl
        self.sort_keys = sort_keys
        self.sorted = sorted if sort_keys else lambda x: x
        self.wrap = wrap
        self.preserve_cr = preserve_cr
        object.__init__(self)

    def encode(self, document):
        if not isinstance(document, dict):
            raise EzTomlEncodeError("Unable to encode {}".format(document))

        stream = TokenStream(indent=self.indent, nl=self.nl)
        tables = self._collect_tables(document)

        for i, table in enumerate(tables):
            if i > 0:
                stream.flush()

            self._write_table(table, stream)

        return stream.__unicode__()

    def _collect_tables(self, current, prefix=(), is_array=False):
        # type: (dict, tuple, bool) -> list[Table]
        current_keys = OrderedDict([])
        collected = []

        for k, v in self.sorted(current.items()):
            path = prefix + (k,)

            if isinstance(v, dict):
                collected.extend(self._collect_tables(v, prefix=path))
            elif isinstance(v, (list, tuple)) and len(v) > 0 and all(isinstance(vv, dict) for vv in v):
                for vv in v:
                    collected.extend(self._collect_tables(vv, prefix=path, is_array=True))
            elif v is not None:
                # toml doesn't have null, so we just skip these
                current_keys[unicode_type(k)] = v

        # only create a parent table if it can't be collapsed/inferred by the c
        if not (len(current) == 1 and isinstance(next(iter(current.values())), dict)):
            # indent all child tables unless we're at the root
            if prefix != ():
                for table in collected:
                    table.depth += 1

                collected.insert(0, Table(prefix, current_keys, is_array))
            elif len(current_keys) > 0:
                collected.insert(0, Table(prefix, current_keys, is_array))

        return collected

    def _write_table(self, table, stream):
        # type: (Table, TokenStream) -> None
        # the top most fields don't need to be indented
        with stream.indented(table.depth):
            if table.path:
                if table.is_array:
                    self._write_array_table_header(table, stream)
                else:
                    self._write_table_header(table, stream)

            if table.kv:
                self._write_kv(list(table.kv.items()), stream)

    def _write_array_table_header(self, table, stream):
        # type: (Table, TokenStream) -> None
        stream.tab()
        stream.append("[[")
        self._write_keys(table.path, stream)
        stream.append("]]")
        stream.flush()

    def _write_key(self, key, stream):  # type: (str, TokenStream) -> None
        return self._encode_key(key, stream)

    def _write_keys(self, keys, stream):  # type: (tuple, TokenStream) -> None
        for i, key in enumerate(keys):
            if i > 0:
                stream.append(".")

            self._write_key(key, stream)

    def _write_table_header(self, table, stream):
        # type: (Table, TokenStream) -> None
        stream.tab()
        stream.append("[")
        self._write_keys(table.path, stream)
        stream.append("]")
        stream.flush()

    def _write_kv(self, kv, stream):
        # type: (list[str, object], TokenStream) -> None
        for k, v in kv:
            stream.tab()
            self._encode_key(k, stream)
            stream.append(" = ")
            self._encode_value(v, stream)
            stream.flush()

    def _encode_key(self, key, stream):
        if isinstance(key, bool):
            return stream.append("true" if key else "false")

        key = unicode_type(key)

        if self._key_regex.match(key) is not None:
            stream.append(key)
        else:
            self._encode_string(key, stream, multiline=False)

    def _encode_string(self, value, stream, multiline=True):
        # type: (str, TokenStream, bool) -> None
        if isinstance(value, bytes):
            try:
                value = value.decode("utf-8")
            except UnicodeDecodeError:
                raise EzTomlEncodeError("Unable to encode bytes: {}".format(repr(value)))

        is_long = len(value) + len(stream._prefix) > 120
        multiline = multiline and ("\n" in value.lstrip() or is_long)

        if self.preserve_cr:
            multiline = multiline and "\r" not in value

        has_double_quote = DQ_INLINE in value
        has_single_quote = SQ_INLINE in value
        has_backslash = "\\" in value
        has_tab = TAB in value

        if not multiline:
            must_escape = any(k in CONTROL_CHARS or should_unicode_escape(k) for k in value)

            if must_escape is False:
                if not has_double_quote and not has_backslash:
                    # can use "..." without any escape needed
                    return self._encode_inline_string(value, stream)

                if not has_single_quote and not has_tab and (has_double_quote or has_backslash):
                    # a raw string is preferred if it has " or \ and doesn't require any other escapes
                    return self._encode_inline_raw_string(value, stream)

            return self._encode_inline_string(value, stream)
        else:
            # strip out \r because we can't make any guarantees
            # and don't want to mix file endings in the target file
            escape_chars = "".join(k for k in CONTROL_CHARS if k not in (DQ_INLINE, NEWLINE)) + TAB
            must_escape = any(k in escape_chars or should_unicode_escape(k) for k in value)

            if not must_escape and (has_backslash and SQ_MULTI not in value):
                return self._encode_multiline_raw_string(value, stream)
            else:
                return self._encode_multiline_string(value, stream)

    def _encode_multiline_raw_string(self, value, stream):  # type: (str, TokenStream) -> None
        stream.append(SQ_MULTI)
        if "\n" in value:
            stream.flush()

        stream.append(value)
        stream.append(SQ_MULTI)

    def _encode_multiline_string(self, value, stream):  # type: (str, TokenStream) -> None
        stream.append(DQ_MULTI)
        stream.flush()

        trailing_nl = value.endswith("\n")
        endswith_space = False

        for i, line in enumerate(value.splitlines()):
            if i > 0:
                # if the previous line ended with a trailing space
                # then manually print out a \n with a \ to make it clear
                # since trailing space is not typically visible
                if endswith_space:
                    stream.append("\\n\\")
                stream.flush()

            line = escape_multi_line(line).replace(DQ_MULTI, '""\\"')
            col = 0
            endswith_space = line.endswith(" ")

            for match in self._word_regex.finditer(line):
                word = match.group()

                if col == 0 or col + len(word) < self.wrap:
                    stream.append(word)
                    col += len(word)
                else:
                    stream.append("\\")
                    stream.flush()
                    stream.append(word)
                    col = len(word)

        if trailing_nl:
            stream.flush()

        stream.append(DQ_MULTI)

    def _encode_inline_raw_string(self, value, stream):  # type: (str, TokenStream) -> None
        stream.append(SQ_INLINE)
        stream.append(value)
        stream.append(SQ_INLINE)

    def _encode_inline_string(self, value, stream):  # type: (str, TokenStream) -> None
        stream.append(DQ_INLINE)
        stream.append(escape(value))
        stream.append(DQ_INLINE)

    def _encode_inline_table(self, value, stream):  # type: (str, TokenStream) -> None
        # determine if it should be split across multiple lines
        multiline = False
        running_length = 0

        for v in value:
            if isinstance(v, (list, tuple)):
                multiline = True
                break
            elif isinstance(v, string_types):
                if "\n" in v:
                    multiline = True
                    break

                running_length += len(v)
                if self.wrap is not None and running_length >= self.wrap:
                    multiline = True
                    break

        multiline = multiline and len(value) > 1
        stream.append("[")

        with stream.indented(delta=int(multiline)):
            for pos, v in enumerate(value):
                if pos != 0:
                    stream.append(",")

                    if not multiline:
                        stream.append(" ")

                if multiline:
                    stream.flush()
                    stream.tab()

                self._encode_value(v, stream)

        if multiline:
            # add a trailing comma
            stream.append(",")
            stream.flush()
            stream.tab()

        stream.append("]")

    def _encode_value(self, value, stream, multiline=True):
        if value is True:
            stream.append("true")
        elif value is False:
            stream.append("false")
        elif isinstance(value, float):
            # use repr() instead of str() because repr maintains precision better
            # for Python 2.7
            stream.append(repr(value))
        elif isinstance(value, number_types):
            stream.append(str(value))
        elif isinstance(value, string_types):
            self._encode_string(value, stream, multiline=multiline)
        elif isinstance(value, dict):
            stream.append("{  ")
            for pos, (k, v) in enumerate(self.sorted(value.items())):
                if pos != 0:
                    stream.append(", ")

                self._encode_key(k, stream)
                stream.append(" = ")
                # don't allow multi-line strings within inline tables
                self._encode_value(v, stream)

            stream.append("}")
        elif isinstance(value, list):
            self._encode_inline_table(value, stream)
        elif isinstance(value, datetime):
            stream.append(value.isoformat())
        elif isinstance(value, time):
            stream.append(str(value))
        elif isinstance(value, date):
            stream.append(str(value))
        else:
            raise EzTomlEncodeError("Unable to encode {}".format(value))
