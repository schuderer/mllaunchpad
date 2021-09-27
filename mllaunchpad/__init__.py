"""Top-level package for ML Launchpad."""

# Stdlib imports
from typing import Dict, Union

# Third-party imports
import pkg_resources

# Project imports
from mllaunchpad import (
    api,
    datasources,
    model_actions,
    model_interface,
    resource,
)
from mllaunchpad.config import get_validated_config, get_validated_config_str
from mllaunchpad.model_actions import _add_to_train_report as report
from mllaunchpad.model_actions import predict, retest, train_model
from mllaunchpad.model_interface import ModelInterface, ModelMakerInterface
from mllaunchpad.resource import order_columns


__version__ = pkg_resources.get_distribution("mllaunchpad").version


def list_models(model_store_location_or_config_dict: Union[Dict, str]):
    """Get information on all available versions of trained models.

    :param model_store_location_or_config_dict: Location of the model store. If you have a config dict available, use that instead.
    :type model_store_location_or_config_dict: Union[Dict, str]

    Side note: The return value includes backups of models that have been re-trained without changing
    the version number (they reside in the subdirectory ``previous``).
    Please note that these backed up models are just listed for information and are not available
    for loading (one would have to restore them by moving them up a directory level from ``previous``.

    Example::

        import mllaunchpad as mllp
        my_cfg = mllp.get_validated_config("./my_config_file.yml")
        all_models = mllp.list_models(my_cfg)  # also accepts model store location string

        # An example of what a ``list_models()``'s result would look like:
        # {
        #     iris: {
        #         1.0.0: { ... complete metadata of this version number ... },
        #         1.1.0: { ... },
        #         latest: { ... duplicate of metadata of highest available version number, here 1.1.0 ... },
        #         backups: [ {...}, {...}, ... ]
        #     },
        #     my_other_model: {
        #         1.0.1: { ... },
        #         2.0.0: { ... },
        #         latest: { ... },
        #         backups: []
        #     }
        # }

    :returns: Dict with information on all available trained models.
    """
    ms = resource.ModelStore(model_store_location_or_config_dict)
    return ms.list_models()


# Make it possible for Sphinx to find the relevant imports
__all__ = [
    "train_model",
    "retest",
    "predict",
    "get_validated_config",
    "get_validated_config_str",
    "ModelInterface",
    "ModelMakerInterface",
    "order_columns",
    "report",
    "list_models",
]
