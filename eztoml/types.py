unicode_type = type(u"")
string_types = str if unicode_type == str else (str, unicode_type)
number_types = int, float, type(int(float("1e100")))


class InlineString(str):
    """Wrapped around ' style inline strings."""


class RawInlineString(str):
    """Wrapped around " style inline strings."""


class MultiLineString(str):
    """Wrapped around ''' style multi-line strings."""


class RawMultiLineString(str):
    """Wrapped around \""" style multi-line strings."""
