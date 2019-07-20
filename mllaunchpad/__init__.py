# -*- coding: utf-8 -*-

"""Top-level package for ML Launchpad."""

__author__ = """Andreas Schuderer"""
__email__ = "pypi@schuderer.net"
__version__ = "0.0.5"

from .api import ModelApi
from .config import get_validated_config
from .model_actions import predict, retest, train_model
from .model_interface import ModelInterface, ModelMakerInterface

# Get rid of stupid pyflakes warning (be warned: redundancy warning):
__all__ = [
    "ModelApi",
    "train_model",
    "retest",
    "predict",
    "get_validated_config",
    "ModelInterface",
    "ModelMakerInterface",
]
