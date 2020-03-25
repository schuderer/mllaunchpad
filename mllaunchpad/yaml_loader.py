# Stdlib imports
import os

# Third-party imports
import yaml


class Loader(yaml.SafeLoader):
    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]

        super().__init__(stream)

    def include(self, node):
        filename = os.path.join(self._root, self.construct_scalar(node))

        with open(filename, "r") as f:
            # Normally, one should use safe_load(), but our Loader
            # is a subclass of yaml.SafeLoader
            return yaml.load(f, Loader)  # nosec


Loader.add_constructor("!include", Loader.include)
