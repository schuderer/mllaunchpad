"""Tests for `mllaunchpad.api` module."""

# Stdlib imports
from unittest import mock

# Third-party imports
import pandas as pd
import pytest
import ramlfications

# Project imports
import mllaunchpad.api as api

from .mock_model import MockModelClass, prediction_output


# from mllaunchpad.model_interface import ModelInterface


# TODO: tests for the API proper (see https://flask.palletsprojects.com/en/1.1.x/testing/)


@pytest.fixture
def app():
    return mock.Mock()


# @pytest.fixture
# def model():
#     class MockModel(ModelInterface):
#         def predict(self, *args):
#             return {}
#
#     yield MockModel()
#
#     del MockModel
#     import gc
#     gc.collect()


def load_model_result(config):
    return (
        MockModelClass(),
        {
            "name": config["model"]["name"],
            "version": config["model"]["version"],
            "created": "2020.02.02",
        },
    )


def parsed_raml(string):
    return ramlfications.parse_raml(
        ramlfications.loads(string), ramlfications.setup_config(None)
    )
    # return ramlfications.parse(string)


minimal_config = {
    "model_store": {"location": "model_store"},
    "model": {"name": "my_model", "version": "1.2.3", "module": "my_module"},
    "api": {"name": "my_api", "raml": "bla.raml"},
}
minimal_config_bad_version = {
    "model_store": {"location": "model_store"},
    "model": {
        "name": "my_model",
        "version": "hey.you.41",
        "module": "my_module",
    },
    "api": {"name": "my_api", "raml": "bla.raml"},
}
raml_head_str = """#%RAML 0.8
---
title: Some API
baseUri: https://{host}/bla/{version}
version: v1
documentation:
    - title: An API
      content: |
        Predicting something
"""
raml_query_resource_str = """

/something:
  get:
    description: Get a prediction something
    queryParameters:
      aparam:
        displayName: a param
        type: string
        description: the param's description
        required: true
"""
raml_resource_id_str = """

/something_else:
  /{test_key}: # just to test
    get:
      queryParameters:
        hallo:
          description: some demo query parameter in addition to the uri param
          type: string
          required: true
          enum: ['metric', 'imperial']
          #default: 42
"""
raml_file_resource_str = """

/some_file:
  post:
    description: Upload a file
    body:
      multipart/form-data:
        formParameters:
          text:
            displayName: Optional alternative text of a client message
            type: string
            description: The plain text of a clients's letter, email, etc (uncleaned)
            required: false
        properties:
          file:
            description: The PDF file containing the client message, to be uploaded
            required: false
            type: file
            fileTypes: ["application/pdf"]
"""
minimal_raml_str = raml_head_str + raml_query_resource_str


@pytest.mark.parametrize(
    "raml",
    [
        raml_head_str + raml_query_resource_str,
        raml_head_str + raml_file_resource_str,
        raml_head_str + raml_query_resource_str + raml_file_resource_str,
        raml_head_str
        + raml_file_resource_str
        + raml_query_resource_str,  # just checking once; order should not matter
        raml_head_str + raml_query_resource_str + raml_file_resource_str,
        raml_head_str
        + raml_file_resource_str
        + raml_query_resource_str.replace(
            "/something:", ""
        ),  # same resource with both query and file functionality
        raml_head_str + raml_resource_id_str,
        raml_head_str + raml_query_resource_str + raml_resource_id_str,
        raml_head_str + raml_file_resource_str + raml_resource_id_str,
        raml_head_str
        + raml_query_resource_str
        + raml_file_resource_str
        + raml_resource_id_str,
    ],
)
@mock.patch("mllaunchpad.api.Api", autospec=True)
@mock.patch(
    "mllaunchpad.resource.ModelStore.load_trained_model",
    side_effect=lambda _: load_model_result(minimal_config),
)
def test_model_modelapi_legal_resource_combinations(
    load_model_mock, api_mock, raml, app
):
    """Should allow between 0 and 3 resources, with 0 or 1 of each resource type."""
    with mock.patch(
        "ramlfications.parse",
        autospec=True,
        side_effect=lambda _: parsed_raml(raml),
    ):
        _ = api.ModelApi(minimal_config, app)
    api_mock.assert_called_once()
    load_model_mock.assert_called_once_with(minimal_config["model"])


@pytest.mark.parametrize(
    "raml",
    [
        raml_head_str
        + raml_query_resource_str
        + raml_query_resource_str.replace("/some", "/some2"),
        raml_head_str
        + raml_query_resource_str
        + raml_file_resource_str
        + raml_file_resource_str.replace("/some", "/some2"),
        raml_head_str
        + raml_query_resource_str
        + raml_resource_id_str
        + raml_resource_id_str.replace("/some", "/some2"),
        raml_head_str
        + raml_query_resource_str
        + raml_resource_id_str
        + raml_resource_id_str.replace("/some", "/some2"),
        raml_head_str
        + raml_file_resource_str
        + raml_file_resource_str.replace("/some", "/some2"),
        raml_head_str
        + raml_file_resource_str
        + raml_query_resource_str
        + raml_query_resource_str.replace("/some", "/some2"),
        raml_head_str
        + raml_file_resource_str
        + raml_resource_id_str
        + raml_resource_id_str.replace("/some", "/some2"),
        raml_head_str
        + raml_resource_id_str
        + raml_resource_id_str.replace("/some", "/some2"),
        raml_head_str
        + raml_resource_id_str
        + raml_file_resource_str
        + raml_file_resource_str.replace("/some", "/some2"),
        raml_head_str
        + raml_resource_id_str
        + raml_query_resource_str
        + raml_query_resource_str.replace("/some", "/some2"),
    ],
)
@mock.patch("mllaunchpad.api.Api", autospec=True)
@mock.patch(
    "mllaunchpad.resource.ModelStore.load_trained_model",
    side_effect=lambda _: load_model_result(minimal_config),
)
def test_model_modelapi_illegal_resource_combinations(
    load_model_mock, api_mock, raml, app
):
    """Should allow between 0 and 3 resources, with 0 or 1 of each resource type."""
    with mock.patch(
        "ramlfications.parse",
        autospec=True,
        side_effect=lambda _: parsed_raml(raml),
    ):
        with pytest.raises(ValueError, match="resources"):
            _ = api.ModelApi(minimal_config, app)
    api_mock.assert_called_once()
    load_model_mock.assert_called_once_with(minimal_config["model"])


@mock.patch(
    "ramlfications.parse",
    autospec=True,
    side_effect=lambda _: parsed_raml(
        minimal_raml_str.replace("version: v1", "version: v99")
    ),
)
@mock.patch("mllaunchpad.api.Api", autospec=True)
@mock.patch(
    "mllaunchpad.resource.ModelStore.load_trained_model",
    side_effect=lambda _: load_model_result(minimal_config),
)
def test_model_modelapi_version_mismatch(
    load_model_mock, api_mock, raml_mock, app
):
    """Should raise error if RAML version does not match major version in config."""
    with pytest.raises(ValueError, match="does not match API version"):
        _ = api.ModelApi(minimal_config, app)


@mock.patch(
    "ramlfications.parse",
    autospec=True,
    side_effect=lambda _: parsed_raml(minimal_raml_str),
)
@mock.patch("mllaunchpad.api.Api", autospec=True)
@mock.patch(
    "mllaunchpad.resource.ModelStore.load_trained_model",
    side_effect=lambda _: load_model_result(minimal_config_bad_version),
)
def test_model_modelapi_malformed_version(
    load_model_mock, api_mock, raml_mock, app
):
    """Should raise error if RAML version does not contain of three integers separated by dots ("0.11.22")."""
    with pytest.raises(ValueError, match="malformed"):
        _ = api.ModelApi(minimal_config_bad_version, app)


@mock.patch(
    "ramlfications.parse",
    autospec=True,
    side_effect=lambda _: parsed_raml(minimal_raml_str),
)
@mock.patch("mllaunchpad.api.Api", autospec=True)
@mock.patch(
    "mllaunchpad.resource.ModelStore.load_trained_model",
    side_effect=lambda _: load_model_result(minimal_config),
)
def test_model_modelapi_predict_using_model(
    load_model_mock, api_mock, raml_mock, app
):
    """Should return expected output."""
    a = api.ModelApi(minimal_config, app)
    output = a.predict_using_model({"a": [1, 2, 3]})
    assert output == prediction_output


def test_generate_raml():
    df = pd.DataFrame({"c1": [1, 2, 3], "c2": ["a", "b", "c"]})

    out = api.generate_raml(
        minimal_config, data_frame=df, resource_name="findme"
    )

    # Should be parseable
    parsed_raml(out)
    assert "/findme" in out
