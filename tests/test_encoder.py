# import eztoml
# import unittest

# from eztoml import Encoder
# from . import test_decoder
#
# print(eztoml.dumps({
#     "a": {
#         "b": {
#             # "hello": "world",
#             "1": 2,
#             "c": {
#                 "3": 4,
#                 "5": 6,
#                 "7": 8,
#                 "d": {
#                     "9": 10,
#                     "11": 12,
#                 }
#             },
#         },
#         "e": {
#             "13": 14,
#             "15": 16,
#             "f": {
#                 "17": 18
#             }
#         }
#     },
#     "f": {},
#     "g": {
#         "h": [
#             {
#                 "19": 20,
#                 "21": 22,
#             },
#             {
#                 "23": 24,
#                 "25": 26,
#                 "27": 28,
#                 "i": {
#                     "29": 30,
#                     "31": 32,
#                 },
#                 "j": {
#                     "33": 34,
#                 }
#             }
#         ]
#     },
#     "custom!key!": {
#         "_": {},
#         "sub k3y$": {
#             "string1": "simple string",
#             "string2": "simple string with apostrophe '",
#             "string3": "simple string with double quote \"",
#             "string4": "simple string with apostrophe' and back \\ slash",
#             "string5": "simple string with double quote\" and back \\ slash",
#             "string6": "simple\nstring\nwith\nmult\u200biple\nlines\n",
#             "string7": "simple string with \nmultiple lines\nand a black \\ slash",
#             "string8": "multiple\nlines\n, oh and three quotes \"\"\", you know.",
#             "string9": "simple string with backspace \b and line feed \f and cr \r and newline \n",
#             "string0": "    \r\t\n   ",
#             "stringa": r'''an example of a multi-line literal string
# * a\b\c\d
# * b
# * c
#
# and then something indented:
#     indented A
#     indented B
#
#             '''
#         }
#     }
# }))
#
