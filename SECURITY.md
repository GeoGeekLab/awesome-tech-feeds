# Security policy

## Reporting a vulnerability

Please report security issues privately through GitHub's security reporting features when available. Do not publish exploit details in a public issue before a fix or mitigation is available.

## Scope

Security reports are especially relevant when registry tooling or CI can:

- read or write outside the repository root;
- execute content supplied by a feed or YAML record;
- expose credentials, tokens, or local configuration;
- follow unsafe URL schemes or unexpected local-network targets;
- consume disproportionate CPU, memory, or network resources from crafted input;
- allow generated artifacts to diverge from validated registry data.

The feed probe treats remote content as untrusted data. It parses RSS, Atom, and JSON Feed; it does not execute embedded scripts.
