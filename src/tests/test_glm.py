from dataclasses import dataclass

import pytest

from datashield_mcp.clients.base import BaseClient


@dataclass
class DummyContext:
    id: str
    session: object


class MockSession:
    def __init__(self):
        self.calls = []

    def aggregate(self, expr: str):
        self.calls.append(expr)
        if expr.startswith("glmDS1("):
            return {
                "server1": [
                    ["meta", 2],
                    ["(Intercept)", "x"],
                    0,
                    [0, 0],
                    0,
                    0,
                    0,
                    "No errors",
                ]
            }
        if expr.startswith("glmDS2("):
            # Use one stable iteration profile that converges after 2 iterations.
            if len([c for c in self.calls if c.startswith("glmDS2(")]) == 1:
                return {
                    "server1": {
                        "info.matrix": [[4.0, 0.0], [0.0, 9.0]],
                        "score.vect": [2.0, -3.0],
                        "dev": 100.0,
                        "Nvalid": 10,
                        "Nmissing": 0,
                        "Ntotal": 10,
                        "numsubs": 10,
                        "family": {"family": "gaussian", "link": "identity"},
                        "disclosure.risk": 0,
                        "errorMessage": "No errors",
                    }
                }
            return {
                "server1": {
                    "info.matrix": [[4.0, 0.0], [0.0, 9.0]],
                    "score.vect": [0.0, 0.0],
                    "dev": 100.0,
                    "Nvalid": 10,
                    "Nmissing": 0,
                    "Ntotal": 10,
                    "numsubs": 10,
                    "family": {"family": "gaussian", "link": "identity"},
                    "disclosure.risk": 0,
                    "errorMessage": "No errors",
                }
            }
        raise AssertionError(f"Unexpected expression: {expr}")


class MockSessionNamedMeta(MockSession):
    def aggregate(self, expr: str):
        self.calls.append(expr)
        if expr.startswith("glmDS1("):
            return {
                "server1": {
                    "value": [
                        {"num.par.glm": 2},
                        ["(Intercept)", "x"],
                        0,
                        [0, 0],
                        0,
                        0,
                        0,
                        "No errors",
                    ]
                }
            }
        return super().aggregate(expr)


def test_get_glm_requires_formula():
    client = BaseClient(DummyContext("test", MockSession()))
    with pytest.raises(ValueError, match="regression formula"):
        client.get_glm(formula=None, family="gaussian")


def test_get_glm_requires_family():
    client = BaseClient(DummyContext("test", MockSession()))
    with pytest.raises(ValueError, match="family"):
        client.get_glm(formula="y ~ x", family=None)


def test_get_glm_runs_and_returns_expected_shape():
    session = MockSession()
    client = BaseClient(DummyContext("test", session))

    result = client.get_glm(formula="y ~ x", family="gaussian", maxit=5, CI=0.95)

    assert result is not None
    assert result["iter"] == 2
    assert result["Nvalid"] == 10
    assert result["Nmissing"] == 0
    assert result["Ntotal"] == 10
    assert result["df"] == 8
    assert result["formula"] == "y ~ x"
    assert isinstance(result["coefficients"], list)
    assert len(result["coefficients"]) == 2
    assert result["coefficients"][0]["name"] == "(Intercept)"

    glm_ds1_calls = [c for c in session.calls if c.startswith("glmDS1(")]
    glm_ds2_calls = [c for c in session.calls if c.startswith("glmDS2(")]
    assert len(glm_ds1_calls) == 1
    assert len(glm_ds2_calls) == 2
    assert glm_ds1_calls[0] == "glmDS1(y ~ x, 'gaussian', NULL, NULL, NULL)"
    assert "glmDS2(y ~ x, 'gaussian'" in glm_ds2_calls[0]


def test_get_glm_parses_named_num_par_glm_shape():
    session = MockSessionNamedMeta()
    client = BaseClient(DummyContext("test", session))

    result = client.get_glm(formula="y ~ x", family="gaussian", maxit=5, CI=0.95)

    assert result is not None
    assert len(result["coefficients"]) == 2
    assert result["coefficients"][0]["name"] == "(Intercept)"
