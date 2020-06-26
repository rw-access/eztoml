"""EzToml time zone handling."""
from datetime import tzinfo, timedelta


class EzTomlTz(tzinfo):
    """RFC-3339 compatible timezone information for TOML."""

    def __init__(self, offset_str):  # type: (str) -> None
        if offset_str == "Z":
            self.delta = timedelta()
        else:
            sign = -1 if offset_str[0] == "-" else 1
            h, m = offset_str[1:].split(":")
            self.delta = sign * timedelta(hours=int(h), minutes=int(m))

    def utcoffset(self, dt):
        """Get the offset from UTC."""
        return self.delta

    def dst(self, dt):
        """Return nothing since RFC-3339 doesn't accept local timezones."""
        return timedelta(0)

    def tzname(self, dt):
        """Convert the timezone to a time string."""
        if self.delta == timedelta():
            return "Z"

        sign = "-" if self.delta < timedelta() else "+"
        delta = abs(self.delta)
        hours = delta.total_seconds() // 60
        minutes = delta.total_seconds() % 60
        return "UTC{sign}{hours:02d}:{minutes:02d}".format(sign=sign, hours=hours, minutes=minutes)
