"""Top-level package for ML Launchpad."""

import pkg_resources

__version__ = pkg_resources.get_distribution("mllaunchpad").version

from mllaunchpad.config import get_validated_config
from mllaunchpad.model_actions import predict, retest, train_model
from mllaunchpad.model_interface import ModelInterface, ModelMakerInterface

# Get rid of stupid pyflakes warning (be warned: redundancy warning):
__all__ = [
    "train_model",
    "retest",
    "predict",
    "get_validated_config",
    "ModelInterface",
    "ModelMakerInterface",
]
