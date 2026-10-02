"""Client-side disclosure policy: analysis plan, object ledger and attack-pattern checks.

Pure logic, no I/O: the proxy feeds it tool calls and records what succeeded.
Server-side DataSHIELD disclosure settings remain the primary control; this is defense in depth.
"""

import json
import re
import time
from collections import Counter, deque
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

# Tools that only touch metadata or session plumbing: allowed before a plan is approved.
META_TOOLS = {
    "list_skills",
    "get_skill",
    "available_servers",
    "open",
    "close",
    "get_errors",
    "list_tables",
    "list_table_variables",
    "list_taxonomies",
    "search_variables",
    "list_resources",
    "list_symbols",
    "remove_symbols",
    "list_colnames",
    "get_classes",
}
# Tools that touch data: must be listed in the approved plan. Anything not in META_TOOLS or DATA_TOOLS is denied.
DATA_TOOLS = {
    "assign_tables",
    "assign_resources",
    "get_length",
    "get_levels",
    "get_dimensions",
    "get_frequencies",
    "get_crosstab",
    "get_quantile_means",
    "get_summary",
    "get_mean",
    "get_histogram",
    "get_correlation",
    "get_glm",
    "tidyverse_select",
    "tidyverse_filter",
    "tidyverse_mutate",
    "tidyverse_arrange",
    "tidyverse_rename",
    "tidyverse_group_by",
    "tidyverse_ungroup",
    "tidyverse_group_keys",
    "tidyverse_distinct",
    "tidyverse_bind_rows",
    "tidyverse_bind_cols",
    "tidyverse_if_else",
    "tidyverse_case_when",
    "tibble_as_tibble",
}
# tidyverse_slice selects rows by position: singling out individuals, never allowed.

ALLOWED_FUNCTIONS = {
    "c", "desc", "starts_with", "ends_with", "contains", "everything", "all_of", "any_of", "where",
    "is.na", "is.numeric", "is.factor", "is.character",
    "as.numeric", "as.integer", "as.factor", "as.character", "factor",
    "log", "log2", "log10", "exp", "sqrt", "abs", "round", "floor", "ceiling",
    "ifelse", "if_else", "case_when", "n", "mean", "median", "sd", "sum", "min", "max",
}  # fmt: skip
GLM_FAMILIES = {"gaussian", "binomial", "poisson"}
R_CONSTANTS = {"TRUE", "FALSE", "T", "F", "NA", "NULL", "Inf", "NaN"}

# ponytail: name-based heuristic, catches id/dob/postcode style names only; pair with variable metadata if needed.
IDENTIFIER_RE = re.compile(
    r"(?:^|[._])(?:id|uid|uuid|identifier|ssn|dob|name|surname|email|phone|address)(?:$|[._])"
    r"|birth|postcode|postal|zipcode",
    re.IGNORECASE,
)
STRING_RE = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
# backticks, statements, assignment, namespaces, slots, indexing, blocks, custom %op%
FORBIDDEN_RE = re.compile(r"`|;|<-|->|::|@|\[|\]|\{|\}|\\|%")
NAME_RE = re.compile(r"(?<![\w.])(?:[A-Za-z]|\.(?![0-9]))[\w.]*")
R_NAME_RE = re.compile(r"^[A-Za-z][\w.]*$")
COMPARISON_RE = re.compile(r"^([A-Za-z.][\w.]*)\s*(>=|<=|>|<)\s*(-?\d+(?:\.\d+)?)$")
REVERSED_RE = re.compile(r"^(-?\d+(?:\.\d+)?)\s*(>=|<=|>|<)\s*([A-Za-z.][\w.]*)$")
FLIP = {">=": "<=", "<=": ">=", ">": "<", "<": ">"}

MAX_SUBSET_DEPTH = 3  # max cumulative filter conditions on one object (progressive narrowing)
MAX_CALLS_PER_MINUTE = 30
MAX_IDENTICAL_CALLS = 2


class PolicyError(Exception):
    pass


class AnalysisPlan(BaseModel):
    """Analysis plan to be approved by a human before any data call."""

    research_question: str = Field(description="The research question, e.g. PICO formulated")
    tables: list[str] = Field(description="Tables or resources to be assigned, as 'project.table'", min_length=1)
    variables: list[str] = Field(description="Variables (columns) used in the analysis", min_length=1)
    subsets: list[str] = Field(
        default=[], description="Exact filter expressions to be used with tidyverse_filter, e.g. 'age >= 40'"
    )
    tools: list[str] = Field(description="Data tools to be called, e.g. get_glm, get_crosstab", min_length=1)
    max_queries: int = Field(default=200, description="Maximum number of data tool calls", ge=1, le=1000)


def _norm(expr: str) -> str:
    return re.sub(r"\s+", "", expr)


def _split_top(expr: str, sep: str) -> list[str]:
    """Split on a separator outside parentheses (string literals are expected to be blanked)."""
    parts, depth, cur = [], 0, ""
    for ch in expr:
        depth += (ch == "(") - (ch == ")")
        if ch == sep and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    return [*parts, cur]


def assigned_names(expr: str) -> list[str]:
    """LHS names of 'a = x, b = y' style expressions (mutate, rename)."""
    blanked = STRING_RE.sub("''", expr)
    return [m.group(1) for p in _split_top(blanked, ",") if (m := re.match(r"\s*([A-Za-z.][\w.]*)\s*=(?!=)", p))]


def parse_conditions(expr: str) -> frozenset[str | tuple]:
    """Split a filter predicate on top-level '&' into numeric comparisons (var, op, value) or opaque strings."""
    conds = set()
    for part in _split_top(STRING_RE.sub(lambda m: m.group(0).replace("&", " "), expr), "&"):
        part = part.strip()
        while part.startswith("(") and part.endswith(")"):
            part = part[1:-1].strip()
        if m := COMPARISON_RE.match(part):
            conds.add((m.group(1), m.group(2), float(m.group(3))))
        elif m := REVERSED_RE.match(part):
            conds.add((m.group(3), FLIP[m.group(2)], float(m.group(1))))
        else:
            conds.add(_norm(part))
    return frozenset(conds)


def near_overlap(a: frozenset, b: frozenset) -> str | None:
    """Two subsets that differ by a single slightly moved threshold isolate a handful of rows (differencing)."""
    only_a, only_b = a - b, b - a
    if len(only_a) != 1 or len(only_b) != 1:
        return None
    (ca,), (cb,) = only_a, only_b
    if not (isinstance(ca, tuple) and isinstance(cb, tuple) and ca[0] == cb[0]):
        return None
    if ca[1][0] != cb[1][0]:  # '>' family vs '<' family: different sides, not a differencing pair
        return None
    # ponytail: fixed tolerance (1 unit or 2%), scale-aware tolerance needs variable distributions
    if abs(ca[2] - cb[2]) <= max(1.0, 0.02 * abs(ca[2])):
        return f"near-overlapping subsets on '{ca[0]}': {ca[1]} {ca[2]:g} vs {cb[1]} {cb[2]:g}"
    return None


@dataclass
class LedgerEntry:
    name: str
    tool: str
    parents: list[str]
    expr: str | None
    root: str
    conditions: frozenset = frozenset()


def validate_plan(plan: AnalysisPlan) -> None:
    unknown = set(plan.tools) - DATA_TOOLS
    if unknown:
        raise PolicyError(f"tools not allowed in a plan: {sorted(unknown)}")
    ids = [v for v in plan.variables if IDENTIFIER_RE.search(v)]
    if ids:
        raise PolicyError(f"identifier-like variables are not allowed: {ids}")
    if plan.subsets and "tidyverse_filter" not in plan.tools:
        raise PolicyError("subsets are declared but tidyverse_filter is not in tools")
    parsed = []
    for s in plan.subsets:
        check_expression(s, set(plan.variables), set())
        conds = parse_conditions(s)
        if len(conds) > MAX_SUBSET_DEPTH:
            raise PolicyError(f"subset '{s}' has more than {MAX_SUBSET_DEPTH} conditions")
        for other, oconds in parsed:
            if reason := near_overlap(conds, oconds):
                raise PolicyError(f"subsets '{other}' and '{s}': {reason}")
        parsed.append((s, conds))


def check_expression(expr: str, variables: set[str], symbols: set[str]) -> None:
    """Allow only allowlisted functions and names from the plan or the ledger."""
    blanked = STRING_RE.sub("''", expr).replace("%in%", " in ")
    if m := FORBIDDEN_RE.search(blanked):
        raise PolicyError(f"forbidden token '{m.group(0)}' in expression: {expr}")
    for m in NAME_RE.finditer(blanked):
        name, rest = m.group(0), blanked[m.end() :].lstrip()
        if IDENTIFIER_RE.search(name):
            raise PolicyError(f"identifier-like name '{name}' in expression: {expr}")
        if rest.startswith("("):
            if name not in ALLOWED_FUNCTIONS:
                raise PolicyError(f"function '{name}' is not allowed")
        elif rest.startswith("=") and not rest.startswith("=="):
            continue  # argument or assigned column name
        elif name not in variables and name not in symbols and name not in R_CONSTANTS and name != "in":
            raise PolicyError(f"'{name}' is not a planned variable nor a known server-side object")


@dataclass
class Policy:
    plan: AnalysisPlan | None = None
    ledger: dict[str, LedgerEntry] = field(default_factory=dict)
    derived: set[str] = field(default_factory=set)  # columns created by mutate/rename
    data_calls: int = 0
    recent: deque = field(default_factory=deque)
    seen: Counter = field(default_factory=Counter)

    def set_plan(self, plan: AnalysisPlan) -> None:
        self.plan = plan
        self.data_calls = 0

    def check(self, tool: str, args: dict, now: float | None = None) -> None:
        """Raise PolicyError if the call must not reach DataSHIELD."""
        if tool in META_TOOLS:
            return
        if tool not in DATA_TOOLS:
            raise PolicyError(f"tool '{tool}' is not allowed")
        if self.plan is None:
            raise PolicyError("no approved analysis plan: call submit_plan and wait for human approval")
        if tool not in self.plan.tools:
            raise PolicyError(f"tool '{tool}' is not in the approved plan")
        self._check_volume(tool, args, time.monotonic() if now is None else now)
        variables = set(self.plan.variables) | self.derived
        for key, value in args.items():
            self._check_arg(tool, key, value, variables)
        if tool == "tidyverse_filter":
            self._check_subset(args["df_name"], args["tidy_expr"])
        self.data_calls += 1

    def _check_volume(self, tool: str, args: dict, now: float) -> None:
        if self.data_calls >= self.plan.max_queries:
            raise PolicyError(f"query budget of the plan exhausted ({self.plan.max_queries})")
        while self.recent and now - self.recent[0] > 60:
            self.recent.popleft()
        if len(self.recent) >= MAX_CALLS_PER_MINUTE:
            raise PolicyError(f"rate limit: more than {MAX_CALLS_PER_MINUTE} data calls per minute")
        key = json.dumps([tool, {k: v for k, v in args.items() if k != "session_id"}], sort_keys=True)
        if self.seen[key] >= MAX_IDENTICAL_CALLS:
            raise PolicyError("identical query repeated too many times")
        self.recent.append(now)
        self.seen[key] += 1

    def _check_arg(self, tool: str, key: str, value, variables: set[str]) -> None:
        if value is None or isinstance(value, bool | int | float) or key == "session_id":
            return
        if key in ("tables", "resources"):
            if bad := [t for t in value.values() if t not in self.plan.tables]:
                raise PolicyError(f"tables not in the approved plan: {bad}")
        elif key in ("df_name", "df_names"):
            if bad := [d for d in ([value] if isinstance(value, str) else value) if d not in self.ledger]:
                raise PolicyError(f"unknown server-side objects: {bad}")
        elif key == "newobj" or (key == "symbol" and tool.startswith("assign_")):
            if not R_NAME_RE.match(value) or IDENTIFIER_RE.search(value):
                raise PolicyError(f"invalid object name '{value}'")
        elif key == "family":
            if value not in GLM_FAMILIES:
                raise PolicyError(f"GLM family '{value}' is not allowed")
        elif isinstance(value, str):
            check_expression(value, variables, set(self.ledger))
            if tool == "tidyverse_rename":
                # new names may not hide an identifier; old names are checked above
                for new in assigned_names(value):
                    if IDENTIFIER_RE.search(new):
                        raise PolicyError(f"invalid column name '{new}'")
        else:
            raise PolicyError(f"unexpected argument '{key}'")

    def _check_subset(self, df_name: str, expr: str) -> None:
        if _norm(expr) not in {_norm(s) for s in self.plan.subsets}:
            raise PolicyError(f"subset '{expr}' is not in the approved plan")
        parent = self.ledger[df_name]
        conds = parent.conditions | parse_conditions(expr)
        if len(conds) > MAX_SUBSET_DEPTH:
            raise PolicyError(f"progressive narrowing: more than {MAX_SUBSET_DEPTH} cumulative subset conditions")
        for entry in self.ledger.values():
            if entry.root == parent.root and (reason := near_overlap(conds, entry.conditions)):
                raise PolicyError(f"differencing: {reason} (existing object '{entry.name}')")

    def record(self, tool: str, args: dict) -> None:
        """Record a successful call in the object ledger."""
        if tool in ("assign_tables", "assign_resources"):
            name = args["symbol"]
            self.ledger[name] = LedgerEntry(
                name, tool, [], json.dumps(args.get("tables") or args.get("resources")), name
            )
            return
        name = args.get("newobj")
        if not name:
            return
        parents = [args["df_name"]] if "df_name" in args else list(args.get("df_names", []))
        expr = args.get("tidy_expr") or args.get("condition") or args.get("cases")
        if tool in ("tidyverse_mutate", "tidyverse_rename"):
            self.derived.update(assigned_names(expr))
        if tool in ("tidyverse_if_else", "tidyverse_case_when"):
            self.derived.add(name)
        if len(parents) == 1 and parents[0] in self.ledger:
            parent = self.ledger[parents[0]]
            conds = parent.conditions | (parse_conditions(expr) if tool == "tidyverse_filter" else frozenset())
            self.ledger[name] = LedgerEntry(name, tool, parents, expr, parent.root, conds)
        else:  # vectors and bound data frames start a new lineage
            self.ledger[name] = LedgerEntry(name, tool, parents, expr, name)
