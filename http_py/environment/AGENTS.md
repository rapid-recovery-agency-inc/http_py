# Environment Module

## Purpose

This module provides type-safe environment variable management using frozen dataclasses. It enables declarative configuration schemas with automatic type coercion, validation, and layered overrides from multiple sources (os.environ, secret managers, config files).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Code                         │
│                                                             │
│    @dataclass(frozen=True)                                  │
│    class AppEnv:                                            │
│        DEBUG: bool = False                                  │
│        DB_HOST: str = "localhost"                           │
│        DB_PORT: int = 5432                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              create_environment(AppEnv)                     │
│  - Creates EnvironmentManager bound to dataclass type       │
│  - Returns manager with env() and set_environment()         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  EnvironmentManager[T]                      │
│  - set_environment(raw): Coerce and merge layer             │
│  - load(raw): Validate mandatory keys, then set             │
│  - env() → T: Build frozen dataclass from state             │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌───────────────┬───────────────┬───────────────┐
│   os.environ  │ Secrets Mgr   │  Config File  │
│   (Layer 1)   │  (Layer 2)    │  (Layer 3)    │
└───────────────┴───────────────┴───────────────┘
        │             │             │
        └─────────────┼─────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   to_dataclass_dict()                       │
│  - Filter keys to dataclass fields only                     │
│  - Apply field-level converters from metadata               │
│  - Coerce values via convert_value()                        │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

| File | Description |
|------|-------------|
| `__init__.py` | Exports `create_environment` and `EnvironmentManager` |
| `factory.py` | `create_environment()` factory function |
| `manager.py` | `EnvironmentManager[T]` generic class for state management |
| `coercion.py` | `convert_value()` and `to_dataclass_dict()` type coercion |
| `validation.py` | `validate_keys()` for mandatory key enforcement |

## Key Components

### EnvironmentManager[T]

Generic manager bound to a frozen dataclass type. Accumulates state from multiple sources with deterministic precedence.

| Method | Description |
|--------|-------------|
| `env()` | Returns a **new** frozen `T` instance from accumulated state |
| `set_environment(raw)` | Coerce and merge raw dict on top of current state |
| `load(raw)` | Validate mandatory keys, then delegate to `set_environment` |

### Type Coercion

The `convert_value()` function handles automatic conversion from strings:

| Target Type | Coercion Behavior |
|-------------|-------------------|
| `str` | Pass-through or `str(value)` |
| `bool` | `value.lower() == "true"` |
| `int` | `int(value)` |
| `float` | `float(value)` |
| `list` | `value.split(",")` or pass-through |
| `set`, `tuple` | `value.split(",")` |
| `dict` | `json.loads(value)` |
| `Enum` | `EnumClass[value]` (by name) |

### Custom Converters

Override default coercion via field metadata:

```python
from dataclasses import dataclass, field

def parse_hosts(value: str) -> list[str]:
    return [h.strip() for h in value.split(",")]

@dataclass(frozen=True)
class AppEnv:
    DB_HOSTS: list[str] = field(
        default_factory=list,
        metadata={"converter": parse_hosts}
    )
```

## Usage Example

```python
# environment.py
import os
from dataclasses import dataclass, field
from http_py.environment import create_environment

@dataclass(frozen=True)
class AppEnv:
    # Required (no default)
    DB_HOST: str
    DB_PASSWORD: str
    
    # Optional with defaults
    DEBUG: bool = False
    DB_PORT: int = 5432
    DB_NAME: str = "app"
    LOG_LEVEL: str = "INFO"

# Create manager once at module level
_manager = create_environment(
    AppEnv,
    mandatory_keys=["DB_HOST", "DB_PASSWORD"],
)

# Export bound methods
env = _manager.env
set_environment = _manager.set_environment
```

```python
# main.py
import os
from myapp.environment import env, set_environment

# Layer 1: Load from os.environ
set_environment(os.environ)

# Layer 2: Override with secrets (later calls win)
secrets = fetch_from_aws_secrets_manager()
set_environment(secrets)

# Access typed config
config = env()
print(f"Connecting to {config.DB_HOST}:{config.DB_PORT}")
print(f"Debug mode: {config.DEBUG}")
```

## Layered Configuration

The module supports deterministic layering where later calls to `set_environment()` override earlier values:

```python
# Base layer: defaults from os.environ
set_environment(os.environ)

# Override layer: secrets take precedence
set_environment(secrets_dict)

# Final override: runtime flags
set_environment({"DEBUG": "true"})
```

State accumulation:
```
Initial:  {}
Layer 1:  {DB_HOST: "prod.db", DEBUG: "false"}
Layer 2:  {DB_HOST: "prod.db", DEBUG: "false", DB_PASSWORD: "secret"}
Layer 3:  {DB_HOST: "prod.db", DEBUG: "true", DB_PASSWORD: "secret"}
```

## Design Principles

1. **Frozen Dataclass Schema**: Configuration shape is defined once, immutably
2. **Explicit Seeding**: No automatic `os.environ` loading — consumers control sources
3. **Layered Overrides**: Later sources override earlier ones deterministically
4. **Type Safety**: All values are coerced to declared types at load time
5. **Fresh Instances**: `env()` returns a new instance each call — no stale references
6. **Field Filtering**: Only dataclass fields are extracted from raw sources

## Future Enhancements

### Planned Features

- [ ] **Validation Decorators**: Field-level validators beyond type coercion
- [ ] **Environment Profiles**: `dev`, `staging`, `prod` profile support
- [ ] **Dotenv Integration**: Built-in `.env` file loading
- [ ] **Secret Manager Adapters**: AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager
- [ ] **Hot Reload**: Watch for environment changes and notify subscribers
- [ ] **Encrypted Fields**: Transparent encryption/decryption for sensitive values
- [ ] **Schema Export**: Generate `.env.example` or JSON Schema from dataclass
- [ ] **Nested Dataclasses**: Support for hierarchical configuration structures
- [ ] **Union Types**: Handle `Optional[T]` and `T | None` patterns

### Extension Points

1. **Custom Type Converters**: Register global converters for custom types
2. **Validation Hooks**: Pre/post validation callbacks
3. **Source Adapters**: Pluggable loaders for various config sources
4. **Change Listeners**: Subscribe to configuration changes

### Migration Notes

When extending the environment schema:
1. Add new fields to the frozen dataclass with sensible defaults
2. Fields without defaults become implicitly required
3. Add to `mandatory_keys` if the field must come from external sources
4. Use `metadata={"converter": fn}` for non-standard type coercion
5. Call `set_environment()` in correct order for desired precedence
