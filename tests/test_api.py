#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `mllaunchpad.api` module."""

# Stdlib imports
from tempfile import NamedTemporaryFile
from unittest.mock import patch

# Third-party imports
import pytest
import ramlfications

# Application imports
import mllaunchpad.api as api
from mllaunchpad.model_interface import ModelInterface


class MockApp:
    def __init__(self):
        pass


@pytest.fixture
def app():
    return MockApp()


class MockModel(ModelInterface):
    def predict(self, *args):
        return {}


@pytest.fixture
def model():
    return MockModel()


def parsed_raml(string):
    with NamedTemporaryFile("w", delete=False) as f:
        f.write(string)
    return ramlfications.parse(f.name)


minimal_config = {
    "model_store": {"location": "model_store"},
    "model": {"name": "my_model", "version": "1.2.3", "module": "my_module"},
    "api": {"name": "my_api", "version": "1.2.3", "raml": "bla.raml"},
}
minimal_raml_str = """#%RAML 0.8
---
title: Some API
baseUri: https://{host}/bla/{version}
version: v0
documentation:
    - title: An API
      content: |
        Predicting something

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


@patch("mllaunchpad.api._load_raml", autospec=True)
@patch("mllaunchpad.api.Api", autospec=True)
@patch("mllaunchpad.resource.ModelStore.load_trained_model")
def test_model_api_init(load_model_mock, api_mock, raml_mock, app, model):
    """Test minimal api initialization."""
    load_model_mock.return_value = (
        model,
        {"name": "my_model", "version": "1.2.3", "created": "2020.02.02"},
    )
    raml_mock.return_value = parsed_raml(minimal_raml_str)
    _ = api.ModelApi(minimal_config, app)


file_raml_str = """#%RAML 0.8
---
title: Some API
baseUri: https://{host}/bla/{version}
version: v0
documentation:
    - title: An API
      content: |
        Predicting something

/something:
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


@patch("mllaunchpad.api._load_raml", autospec=True)
@patch("mllaunchpad.api.Api", autospec=True)
@patch("mllaunchpad.resource.ModelStore.load_trained_model")
def test_model_api_fileraml(load_model_mock, api_mock, raml_mock, app, model):
    """Test minimal api initialization."""
    load_model_mock.return_value = (
        model,
        {"name": "my_model", "version": "1.2.3", "created": "2020.02.02"},
    )
    raml_mock.return_value = parsed_raml(file_raml_str)
    _ = api.ModelApi(minimal_config, app)
