"""DataSHIELD guard: an MCP proxy that enforces an approved analysis plan in front of the DataSHIELD MCP server.

The model only sees this proxy. Plans are approved by a human with `datashield-guard approve <plan_id>`.
"""

import argparse
import getpass
import json
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import anyio
from mcp import Client
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolRequestParams, CallToolResult, ListToolsResult, TextContent, Tool
from pydantic import ValidationError

from datashield_mcp.guard.policy import DATA_TOOLS, META_TOOLS, AnalysisPlan, Policy, PolicyError, validate_plan
from datashield_mcp.logs import log_dir, logger

PLANS_DIR = log_dir.parent / "plans"
AUDIT_DIR = log_dir.parent / "audit"
MAX_LOGGED_TEXT = 10_000

GUARD_TOOLS = [
    Tool(
        name="submit_plan",
        description=(
            "Submit the analysis plan for human approval. Required before any data tool call "
            "(assign, summaries, models, tidyverse operations). Only the declared tables, variables, subsets "
            "and tools will be allowed. Submitting a new plan revokes the current one."
        ),
        input_schema={"type": "object", "properties": {"plan": AnalysisPlan.model_json_schema()}, "required": ["plan"]},
    ),
    Tool(
        name="get_plan_status",
        description="Get the status (pending, approved) of the last submitted analysis plan.",
        input_schema={"type": "object", "properties": {}},
    ),
]


def now() -> str:
    return datetime.now(UTC).isoformat()


class Audit:
    """Append-only JSON lines audit trail, one file per guard session."""

    def __init__(self, session: str):
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        self.session = session
        self.path = AUDIT_DIR / f"{session}.jsonl"

    def log(self, event: str, **data: Any) -> None:
        with self.path.open("a") as f:
            f.write(json.dumps({"ts": now(), "session": self.session, "event": event, **data}, default=str) + "\n")


def plan_path(plan_id: str):
    if not plan_id.isalnum():
        raise ValueError(f"invalid plan id: {plan_id}")
    return PLANS_DIR / f"{plan_id}.json"


@dataclass
class GuardState:
    client: Client
    policy: Policy
    audit: Audit
    plan_id: str | None = None


def text_result(text: str, error: bool = False) -> CallToolResult:
    return CallToolResult(content=[TextContent(type="text", text=text)], is_error=error)


def result_for_audit(result: CallToolResult) -> list[str]:
    return [c.text[:MAX_LOGGED_TEXT] if isinstance(c, TextContent) else f"<{c.type}>" for c in result.content]


def make_server(upstream) -> Server:
    @asynccontextmanager
    async def lifespan(_: Server) -> AsyncIterator[GuardState]:
        audit = Audit(uuid.uuid4().hex)
        audit.log("start", upstream=upstream if isinstance(upstream, str) else "in-process")
        async with Client(upstream) as client:
            yield GuardState(client, Policy(), audit)
        audit.log("stop")

    async def list_tools(ctx, params) -> ListToolsResult:
        upstream_tools = (await ctx.lifespan_context.client.list_tools()).tools
        return ListToolsResult(tools=[t for t in upstream_tools if t.name in META_TOOLS | DATA_TOOLS] + GUARD_TOOLS)

    async def call_tool(ctx, params: CallToolRequestParams) -> CallToolResult:
        state: GuardState = ctx.lifespan_context
        args = params.arguments or {}
        if params.name == "submit_plan":
            return submit_plan(state, args.get("plan"))
        if params.name == "get_plan_status":
            return text_result(json.dumps(refresh_plan(state)))
        refresh_plan(state)
        try:
            state.policy.check(params.name, args)
        except PolicyError as e:
            state.audit.log("call_denied", tool=params.name, args=args, reason=str(e), plan_id=state.plan_id)
            return text_result(f"Denied by DataSHIELD guard: {e}", error=True)
        state.audit.log("call", tool=params.name, args=args, plan_id=state.plan_id)
        result = await state.client.call_tool(params.name, args)
        state.audit.log("result", tool=params.name, is_error=result.is_error, content=result_for_audit(result))
        if not result.is_error:
            state.policy.record(params.name, args)
        return result

    return Server("DataSHIELD guard", lifespan=lifespan, on_list_tools=list_tools, on_call_tool=call_tool)


def submit_plan(state: GuardState, raw: Any) -> CallToolResult:
    try:
        plan = AnalysisPlan.model_validate(raw)
        validate_plan(plan)
    except (ValidationError, PolicyError) as e:
        state.audit.log("plan_rejected", plan=raw, reason=str(e))
        return text_result(f"Plan rejected: {e}", error=True)
    state.plan_id = uuid.uuid4().hex[:12]
    state.policy.plan = None  # revoke the current plan until the new one is approved
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    record = {"id": state.plan_id, "status": "pending", "submitted_at": now(), "session": state.audit.session}
    plan_path(state.plan_id).write_text(json.dumps({**record, "plan": plan.model_dump()}, indent=2))
    state.audit.log("plan_submitted", plan_id=state.plan_id, plan=plan.model_dump())
    return text_result(
        f"Plan {state.plan_id} submitted. Ask the user to review and approve it in a terminal with: "
        f"datashield-guard approve {state.plan_id}. Then check get_plan_status."
    )


def refresh_plan(state: GuardState) -> dict:
    """Activate the submitted plan once a human has approved it (approval happens outside the model's reach)."""
    if state.plan_id is None:
        return {"status": "none"}
    record = json.loads(plan_path(state.plan_id).read_text())
    if record["status"] == "approved" and state.policy.plan is None:
        state.policy.set_plan(AnalysisPlan.model_validate(record["plan"]))
        state.audit.log("plan_approved", plan_id=state.plan_id, by=record.get("approved_by"))
    return {"plan_id": state.plan_id, "status": record["status"]}


def approve(plan_id: str) -> None:
    path = plan_path(plan_id)
    record = json.loads(path.read_text())
    print(json.dumps(record["plan"], indent=2))
    if input(f"Approve plan {plan_id}? [y/N] ").strip().lower() != "y":
        print("Not approved.")
        return
    record.update(status="approved", approved_by=getpass.getuser(), approved_at=now())
    path.write_text(json.dumps(record, indent=2))
    print(f"Plan {plan_id} approved.")


async def serve(upstream) -> None:
    server = make_server(upstream)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    parser = argparse.ArgumentParser(description="DataSHIELD guard: plan-enforcing MCP proxy")
    sub = parser.add_subparsers(dest="command")
    serve_cmd = sub.add_parser("serve", help="Run the proxy over stdio (default)")
    serve_cmd.add_argument("--upstream", help="DataSHIELD MCP URL (default: run the DataSHIELD MCP server in-process)")
    sub.add_parser("list", help="List submitted plans")
    approve_cmd = sub.add_parser("approve", help="Review and approve a submitted plan")
    approve_cmd.add_argument("plan_id")
    args = parser.parse_args()

    if args.command == "approve":
        approve(args.plan_id)
    elif args.command == "list":
        for path in sorted(PLANS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime):
            record = json.loads(path.read_text())
            print(record["id"], record["status"], record["submitted_at"], record["plan"]["research_question"])
    else:
        upstream = getattr(args, "upstream", None)
        if upstream is None:
            from datashield_mcp.server import mcp as upstream
        try:
            anyio.run(serve, upstream)
        except KeyboardInterrupt:
            logger.info("Guard stopped.")


if __name__ == "__main__":
    main()
