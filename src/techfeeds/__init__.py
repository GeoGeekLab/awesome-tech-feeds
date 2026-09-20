"""Awesome Tech Feeds registry tooling and public consumer SDK."""

from .consumer import (
    DEFAULT_REGISTRY_URL,
    ConsumerError,
    Query,
    QueryContractError,
    QueryResult,
    Registry,
    RegistryCompatibilityError,
    RegistryIntegrityError,
    RegistryLoadError,
    SourceRecord,
    UnknownFilterValueError,
)

__version__ = "0.4.0"

__all__ = [
    "DEFAULT_REGISTRY_URL",
    "ConsumerError",
    "Query",
    "QueryContractError",
    "QueryResult",
    "Registry",
    "RegistryCompatibilityError",
    "RegistryIntegrityError",
    "RegistryLoadError",
    "SourceRecord",
    "UnknownFilterValueError",
    "__version__",
]
