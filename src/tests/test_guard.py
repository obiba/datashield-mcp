"""Tests for the DataSHIELD guard: policy checks on malicious query sequences, and the proxy end to end."""

import json

import anyio
import pytest
from mcp import Client
from mcp.server.mcpserver import MCPServer

from datashield_mcp.guard import proxy
from datashield_mcp.guard.policy import AnalysisPlan, Policy, PolicyError, validate_plan

PLAN = AnalysisPlan(
    research_question="Is BMI associated with diabetes in adults?",
    tables=["CNSIM.CNSIM1"],
    variables=["LAB_GLUC", "PM_BMI_CONTINUOUS", "DIS_DIAB", "GENDER", "age"],
    subsets=["age >= 40", "age < 40", "GENDER == 1"],
    tools=["assign_tables", "tidyverse_filter", "tidyverse_mutate", "get_mean", "get_dimensions", "get_glm"],
)


def approved_policy() -> Policy:
    policy = Policy()
    policy.set_plan(PLAN)
    policy.check("assign_tables", {"session_id": "s", "symbol": "D", "tables": {"site1": "CNSIM.CNSIM1"}})
    policy.record("assign_tables", {"session_id": "s", "symbol": "D", "tables": {"site1": "CNSIM.CNSIM1"}})
    return policy


def call(policy: Policy, tool: str, **args) -> None:
    policy.check(tool, {"session_id": "s", **args})
    policy.record(tool, args)


def test_no_plan_blocks_data_but_not_metadata():
    policy = Policy()
    policy.check("list_tables", {"session_id": "s"})
    with pytest.raises(PolicyError, match="no approved analysis plan"):
        policy.check("get_mean", {"session_id": "s", "symbol": "D$age"})


def test_unknown_and_slice_tools_denied():
    policy = approved_policy()
    for tool in ("tidyverse_slice", "datashield_assign_expr"):
        with pytest.raises(PolicyError, match="not allowed"):
            policy.check(tool, {"session_id": "s"})


def test_out_of_plan_calls_denied():
    policy = approved_policy()
    with pytest.raises(PolicyError, match="not in the approved plan"):
        policy.check("get_crosstab", {"session_id": "s", "symbol_x": "D$GENDER", "symbol_y": "D$DIS_DIAB"})
    with pytest.raises(PolicyError, match="not a planned variable"):
        policy.check("get_mean", {"session_id": "s", "symbol": "D$LAB_TRIG"})
    with pytest.raises(PolicyError, match="tables not in the approved plan"):
        policy.check("assign_tables", {"session_id": "s", "symbol": "E", "tables": {"site1": "CNSIM.CNSIM2"}})
    with pytest.raises(PolicyError, match="not in the approved plan"):
        policy.check("tidyverse_filter", {"session_id": "s", "df_name": "D", "tidy_expr": "age >= 65", "newobj": "X"})


def test_identifiers_denied():
    with pytest.raises(PolicyError, match="identifier-like"):
        validate_plan(PLAN.model_copy(update={"variables": [*PLAN.variables, "patient_id"]}))
    with pytest.raises(PolicyError, match="identifier-like"):
        validate_plan(PLAN.model_copy(update={"variables": [*PLAN.variables, "date_of_birth"]}))
    policy = approved_policy()
    with pytest.raises(PolicyError, match="identifier-like"):
        policy.check("get_mean", {"session_id": "s", "symbol": "D$postcode"})


def test_free_form_expressions_denied():
    policy = approved_policy()
    for expr in (
        "system('cat /etc/passwd')",
        "D$age[1]",
        "base::get('D')",
        "`D`$age",
        "x <- D$age",
        "D$age %o% D$age",
    ):
        with pytest.raises(PolicyError):
            policy.check("get_mean", {"session_id": "s", "symbol": expr})
    with pytest.raises(PolicyError, match="family"):
        policy.check("get_glm", {"session_id": "s", "formula": "D$DIS_DIAB ~ D$age", "family": "quasi"})


def test_plan_with_near_overlapping_subsets_rejected():
    validate_plan(PLAN)
    for subsets in (["age >= 40", "age >= 41"], ["age >= 40", "age > 40"], ["age >= 40", "39.5 <= age"]):
        with pytest.raises(PolicyError, match="near-overlapping"):
            validate_plan(PLAN.model_copy(update={"subsets": subsets}))


def test_differencing_across_calls_detected():
    # The plan was approved with distinct subsets; reaching a near-overlap through the ledger is still caught.
    policy = Policy()
    policy.set_plan(PLAN.model_copy(update={"subsets": ["age >= 40", "age >= 41", "GENDER == 1"]}))
    call(policy, "assign_tables", symbol="D", tables={"site1": "CNSIM.CNSIM1"})
    call(policy, "tidyverse_filter", df_name="D", tidy_expr="age >= 40", newobj="A")
    with pytest.raises(PolicyError, match="differencing"):
        policy.check("tidyverse_filter", {"session_id": "s", "df_name": "D", "tidy_expr": "age >= 41", "newobj": "B"})


def test_progressive_narrowing_detected():
    policy = Policy()
    policy.set_plan(
        PLAN.model_copy(update={"subsets": ["age >= 40", "GENDER == 1", "DIS_DIAB == 1", "PM_BMI_CONTINUOUS > 35"]})
    )
    call(policy, "assign_tables", symbol="D", tables={"site1": "CNSIM.CNSIM1"})
    call(policy, "tidyverse_filter", df_name="D", tidy_expr="age >= 40", newobj="A")
    call(policy, "tidyverse_filter", df_name="A", tidy_expr="GENDER == 1", newobj="B")
    call(policy, "tidyverse_filter", df_name="B", tidy_expr="DIS_DIAB == 1", newobj="C")
    with pytest.raises(PolicyError, match="progressive narrowing"):
        policy.check(
            "tidyverse_filter",
            {"session_id": "s", "df_name": "C", "tidy_expr": "PM_BMI_CONTINUOUS > 35", "newobj": "E"},
        )


def test_derived_columns_and_ledger():
    policy = approved_policy()
    call(policy, "tidyverse_mutate", df_name="D", tidy_expr="bmi2 = PM_BMI_CONTINUOUS ^ 2", newobj="D2")
    policy.check("get_mean", {"session_id": "s", "symbol": "D2$bmi2"})
    assert policy.ledger["D2"].root == "D"
    with pytest.raises(PolicyError, match="unknown server-side objects"):
        policy.check("tidyverse_filter", {"session_id": "s", "df_name": "Z", "tidy_expr": "age >= 40", "newobj": "X"})


def test_query_volume_limits():
    policy = approved_policy()
    policy.check("get_mean", {"session_id": "s", "symbol": "D$age"})
    policy.check("get_mean", {"session_id": "s", "symbol": "D$age"})
    with pytest.raises(PolicyError, match="repeated"):
        policy.check("get_mean", {"session_id": "s", "symbol": "D$age"})
    policy = approved_policy()
    with pytest.raises(PolicyError, match="rate limit"):
        for i in range(40):
            policy.check(
                "get_glm", {"session_id": "s", "formula": "D$DIS_DIAB ~ D$age", "family": "binomial", "maxit": i}
            )


def fake_datashield() -> MCPServer:
    """Fake site: answers with canned values, records what reached it."""
    fake = MCPServer("fake DataSHIELD")
    fake.reached = []

    @fake.tool()
    def list_tables(session_id: str) -> dict:
        fake.reached.append("list_tables")
        return {"site1": ["CNSIM.CNSIM1"]}

    @fake.tool()
    def assign_tables(session_id: str, symbol: str, tables: dict[str, str]) -> dict:
        fake.reached.append("assign_tables")
        return {"site1": [symbol]}

    @fake.tool()
    def get_mean(session_id: str, symbol: str) -> dict:
        fake.reached.append("get_mean")
        return {"site1": 42.0}

    @fake.tool()
    def tidyverse_slice(session_id: str, df_name: str, tidy_expr: str, newobj: str) -> dict:
        fake.reached.append("tidyverse_slice")
        return {}

    return fake


def test_proxy_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(proxy, "PLANS_DIR", tmp_path / "plans")
    monkeypatch.setattr(proxy, "AUDIT_DIR", tmp_path / "audit")
    fake = fake_datashield()

    async def scenario():
        async with Client(proxy.make_server(fake)) as client:
            names = {t.name for t in (await client.list_tools()).tools}
            assert names == {"list_tables", "assign_tables", "get_mean", "submit_plan", "get_plan_status"}

            assert not (await client.call_tool("list_tables", {"session_id": "s"})).is_error
            denied = await client.call_tool("get_mean", {"session_id": "s", "symbol": "D$age"})
            assert denied.is_error and "no approved analysis plan" in denied.content[0].text

            plan = PLAN.model_copy(update={"tools": ["assign_tables", "get_mean"], "subsets": []}).model_dump()
            submitted = await client.call_tool("submit_plan", {"plan": plan})
            plan_id = submitted.content[0].text.split()[1]
            assert (await client.call_tool("assign_tables", {"session_id": "s", "symbol": "D", "tables": {}})).is_error

            # human approval, out of the model's reach
            path = tmp_path / "plans" / f"{plan_id}.json"
            path.write_text(json.dumps({**json.loads(path.read_text()), "status": "approved"}))

            assign = {"session_id": "s", "symbol": "D", "tables": {"site1": "CNSIM.CNSIM1"}}
            assert not (await client.call_tool("assign_tables", assign)).is_error
            mean = await client.call_tool("get_mean", {"session_id": "s", "symbol": "D$age"})
            assert not mean.is_error and "42" in mean.content[0].text
            slice_ = {"session_id": "s", "df_name": "D", "tidy_expr": "1", "newobj": "X"}
            assert (await client.call_tool("tidyverse_slice", slice_)).is_error

    anyio.run(scenario)
    assert fake.reached == ["list_tables", "assign_tables", "get_mean"]
    (audit,) = (tmp_path / "audit").glob("*.jsonl")
    events = [json.loads(line)["event"] for line in audit.read_text().splitlines()]
    assert events == [
        "start",
        "call",
        "result",
        "call_denied",
        "plan_submitted",
        "call_denied",
        "plan_approved",
        "call",
        "result",
        "call",
        "result",
        "call_denied",
        "stop",
    ]
