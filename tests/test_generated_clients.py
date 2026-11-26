"""Every function of the generated API clients must be importable and its type hints resolvable.

Python 3.14 evaluates annotations late, so a name the generator forgot to import (for example `Unset`) only fails on
3.13 and older, which CI and many users run. `typing.get_type_hints` evaluates the hints on every version, so this
catches it everywhere.

Run with:
    pytest -m unit tests/test_generated_clients.py
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import typing
from types import ModuleType

import publisher_client.api
import pytest

from ce.iir.api.iir_client import api as iir_api

pytestmark = pytest.mark.unit


def endpoint_modules(package: ModuleType) -> list[ModuleType]:
    """Every module under package.api: one per endpoint."""
    return [
        importlib.import_module(info.name)
        for info in pkgutil.walk_packages(package.__path__, package.__name__ + ".")
        if not info.ispkg
    ]


@pytest.mark.parametrize(
    "package", [publisher_client.api, iir_api], ids=["publisher", "iir"]
)
def test_the_type_hints_of_every_endpoint_resolve(package: ModuleType) -> None:
    modules = endpoint_modules(package)
    assert modules, "no endpoint modules found"

    for module in modules:
        for name, function in vars(module).items():
            if inspect.isfunction(function) and function.__module__ == module.__name__:
                try:
                    typing.get_type_hints(function)
                except NameError as error:
                    pytest.fail(f"{module.__name__}.{name}: {error}")
