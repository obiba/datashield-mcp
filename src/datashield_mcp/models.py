from dataclasses import dataclass
from datashield import DSSession


@dataclass
class DSContext:
    """Context for DataSHIELD sessions"""

    id: str
    session: DSSession


@dataclass
class AppContext:
    """Application context with typed dependencies."""

    sessions: dict[str, DSContext]
