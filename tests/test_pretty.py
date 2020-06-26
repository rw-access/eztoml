import io
import os
import unittest

import eztoml

test_dir = os.path.dirname(os.path.abspath(__file__))


class TestPrettyFormatting(unittest.TestCase):
    def assert_pretty(self, original_path, pretty_path):

        with io.open(os.path.join(test_dir, "files", original_path), "r") as f:
            original = eztoml.load(f)

        with io.open(os.path.join(test_dir, "files", pretty_path), "r") as f:
            pretty_str = f.read()
            expected_pretty = eztoml.loads(pretty_str)

        self.assertDictEqual(original, expected_pretty)

        encoded = eztoml.dumps(original, sort_keys=True, indent=2)
        self.assertEqual(encoded, pretty_str)

    def test_pretty_format(self):
        self.assert_pretty("example.toml", "example.pretty.toml")
        self.assert_pretty("example-v0.3.0.toml", "example-v0.3.0.pretty.toml")
        self.assert_pretty("example-v0.4.0.toml", "example-v0.4.0.pretty.toml")
        self.assert_pretty("fruit.toml", "fruit.pretty.toml")
        self.assert_pretty("hard_example.toml", "hard_example.pretty.toml")
