# Stdlib imports
import os

# Third-party imports
import yaml


class SafeIncludeLoader(yaml.SafeLoader):
    """A subclass of SafeLoader which supports !include file references."""

    def __init__(self, stream):
        if isinstance(stream, str) or isinstance(stream, bytes):
            # Loading config from string
            self._root = "."
        else:
            # Loading config from file
            self._root = os.path.split(stream.name)[0]

        super().__init__(stream)

    def include(self, node):
        filename = os.path.join(self._root, self.construct_scalar(node))

        with open(filename, "r", encoding="utf-8") as f:
            # Normally, one should use safe_load(), but our Loader
            # is a subclass of yaml.SafeLoader
            return yaml.load(f, Loader=SafeIncludeLoader)  # nosec


SafeIncludeLoader.add_constructor("!include", SafeIncludeLoader.include)
