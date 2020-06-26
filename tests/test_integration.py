import eztoml
import unittest
import yaml
import io
import os

import eztoml.source

src = eztoml.source.Source
test_dir = os.path.dirname(os.path.abspath(__file__))


def read_test_file(name):
    with io.open(os.path.join(test_dir, "files", name), "r") as toml_src:
        return toml_src.read()


class TestDecoder(unittest.TestCase):

    decoder = eztoml.Decoder()

    def check(self, toml_path, yaml_path):
        toml_contents = read_test_file(toml_path)
        yaml_contents = read_test_file(yaml_path)

        toml_decoded = eztoml.loads(toml_contents)
        yaml_decoded = yaml.safe_load(yaml_contents)

        self.assertEqual(toml_decoded, yaml_decoded)

    def test_all(self):
        self.check("example.toml", "example.yaml")
        self.check("fruit.toml", "fruit.yaml")
        self.check("hard_example.toml", "hard_example.yaml")

    def test_parse(self):
        toml_contents = read_test_file("example-v0.3.0.toml")
        eztoml.loads(toml_contents)

        toml_contents = read_test_file("example-v0.4.0.toml")
        eztoml.loads(toml_contents)
