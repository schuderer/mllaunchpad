"""Tests for `mllaunchpad.resource` module."""

# Stdlib imports
import json
from collections import OrderedDict

# Third-party imports
import numpy as np
import pandas as pd
import pytest

# Project imports
from mllaunchpad import resource as r


# fmt: off
ndarray_examples = [
    3,
    [1, 2, 3],
    [[1, 2], [3, 4]],
    [[[1, 2]], [[3, 4]]],
    [[.1, .2], [.3, .4]],
]
dataframe_examples = [
    (pd.DataFrame(), {}),
    (pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]}),
        {'x': {0: 1, 1: 2, 2: 3}, 'y': {0: 4, 1: 5, 2: 6}})
]
mixed_examples = [
    ["a", 3, 3.7, [7], {"hello": 4, "something": ["else", "here", 12]}],
    [np.array(e) for e in ndarray_examples],
    {i: np.array(e) for i, e in enumerate(ndarray_examples)},
    ["a", 3, np.array([4, 5]), pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})],
]
# fmt: on


@pytest.mark.parametrize(
    "test_input,expected",
    zip([np.array(e) for e in ndarray_examples], ndarray_examples),
)
def test_to_plain_python_obj_numpy(test_input, expected):
    """Test to convert numpy arrays to json-compatible object."""
    output = r.to_plain_python_obj(test_input)
    assert output == expected
    # We should not get a json conversion error
    json.dumps(output)


@pytest.mark.parametrize("test_input,expected", dataframe_examples)
def test_to_plain_python_obj_pandas(test_input, expected):
    """Test to convert pandas arrays to json-compatible object."""
    output = r.to_plain_python_obj(test_input)
    assert output == expected
    # We should not get a json conversion error
    json.dumps(output)


@pytest.mark.parametrize("test_input", mixed_examples)
def test_to_plain_python_obj_mixed(test_input):
    """Test to convert mixed arrays to json-compatible object."""
    # It's enough that we don't get an exception here
    output = r.to_plain_python_obj(test_input)
    # We should not get a json conversion error
    json.dumps(output)


def test_to_plain_python_obj_error():
    """Test the error case."""

    class FailingObject:
        pass

    output = r.to_plain_python_obj(FailingObject())
    with pytest.raises(TypeError):
        json.dumps(output)


def test_order_columns_dict():
    d = {"c": [1, 2, 3], "b": [4, 5, 6], "a": [7, 8, 9]}
    expected = OrderedDict(a=[7, 8, 9], b=[4, 5, 6], c=[1, 2, 3])
    output = r.order_columns(d)
    assert output == expected
    assert list(output.keys()) == list(expected.keys())
    assert isinstance(output, type(expected))


def test_order_columns_df():
    df = pd.DataFrame(OrderedDict(c=[1, 2, 3], b=[4, 5, 6], a=[7, 8, 9]))
    expected = pd.DataFrame(OrderedDict(a=[7, 8, 9], b=[4, 5, 6], c=[1, 2, 3]))
    output = r.order_columns(df)
    pd.testing.assert_frame_equal(output, expected)


def test_order_columns_np():
    a = np.array(
        [(1, 4, 7), (2, 5, 8), (3, 6, 9)],
        dtype=[("c", "i4"), ("b", "i4"), ("a", "i4")],
    )
    expected = np.array(
        [(7, 4, 1), (8, 5, 2), (9, 6, 3)],
        dtype=[("a", "i4"), ("b", "i4"), ("c", "i4")],
    )

    # ordinary structured array
    output = r.order_columns(a)
    pd.testing.assert_frame_equal(pd.DataFrame(output), pd.DataFrame(expected))

    # record array
    a_r = np.rec.array(a)
    expected_r = np.rec.array(expected)
    output_r = r.order_columns(a_r)
    pd.testing.assert_frame_equal(
        pd.DataFrame(output_r), pd.DataFrame(expected_r)
    )


def test_order_columns_np_not_structured():
    a = np.array([(1, 4, 7), (2, 5, 8), (3, 6, 9)])
    with pytest.raises(TypeError):
        r.order_columns(a)


def test_order_columns_unsupported():
    with pytest.raises(TypeError):
        r.order_columns(["Hello", "there"])
