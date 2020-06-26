unicode_type = type(u"")
string_types = str if unicode_type == str else (str, unicode_type)
number_types = int, float, type(int(float("1e100")))
