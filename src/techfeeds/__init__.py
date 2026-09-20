"""Awesome Tech Feeds registry tooling and public consumer SDK."""

from .consumer import (
    DEFAULT_REGISTRY_URL,
    ConsumerError,
    ProfileRecord,
    ProfileResult,
    ProfileSource,
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

__version__ = "0.5.0"

__all__ = [
    "DEFAULT_REGISTRY_URL",
    "ConsumerError",
    "ProfileRecord",
    "ProfileResult",
    "ProfileSource",
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
