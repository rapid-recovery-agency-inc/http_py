"""Examples: modules.environment library usage.

Run with:  python examples.py
"""

import os
from typing import Literal
from dataclasses import field, dataclass

from modules.environment import create_environment


# ──────────────────────────────────────────────────────────────────────
# 1. Custom converter via field metadata
# ──────────────────────────────────────────────────────────────────────
#
# Any field that needs non-standard coercion can declare a converter
# in its ``metadata`` dict.  The converter receives the raw value and
# must return the coerced result.

BooleanString = Literal["true", "false"]


def to_boolean_string(value: bool | int | str) -> BooleanString:
    """Convert various truthy/falsy representations to "true"/"false"."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return "true" if value == 1 else "false"
    return "true" if str(value).lower() == "true" else "false"


@dataclass(frozen=True)
class AppEnvironment:
    """A sample frozen dataclass defining the environment shape."""

    DEBUG: bool = False
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "mydb"
    FEATURE_FLAG: BooleanString = field(
        default="false",
        metadata={"converter": to_boolean_string},
    )


# ──────────────────────────────────────────────────────────────────────
# 2. Bootstrap — call create_environment once
# ──────────────────────────────────────────────────────────────────────

_manager = create_environment(AppEnvironment)
env = _manager.env
set_environment = _manager.set_environment


def main() -> None:
    # Before any set_environment call, env() returns all defaults.
    print("── defaults ──")
    print(env())
    # AppEnvironment(DEBUG=False, DB_HOST='localhost', DB_PORT=5432,
    #                DB_NAME='mydb', FEATURE_FLAG='false')

    # ──────────────────────────────────────────────────────────────
    # 3. Seeding from os.environ (explicit)
    # ──────────────────────────────────────────────────────────────
    os.environ["DB_HOST"] = "prod-db.example.com"
    os.environ["DB_PORT"] = "5433"
    os.environ["FEATURE_FLAG"] = "true"

    set_environment(os.environ)

    print("\n── after set_environment(os.environ) ──")
    print(env())
    # DB_HOST='prod-db.example.com', DB_PORT=5433, FEATURE_FLAG='true'

    # ──────────────────────────────────────────────────────────────
    # 4. Layering: later calls override earlier values
    # ──────────────────────────────────────────────────────────────
    # Simulate a secret-manager payload that overrides DB_HOST
    # but leaves everything else intact.
    secret_manager_values = {
        "DB_HOST": "secret-db.internal",
        "DB_NAME": "production",
    }
    set_environment(secret_manager_values)

    print("\n── after set_environment(secret_manager_values) ──")
    snapshot = env()
    print(snapshot)
    # DB_HOST is now 'secret-db.internal' (overridden by 2nd call)
    # DB_PORT is still 5433 (from 1st call, not overridden)
    assert snapshot.DB_HOST == "secret-db.internal"
    assert snapshot.DB_NAME == "production"
    assert snapshot.DB_PORT == 5433  # retained from first call

    # ──────────────────────────────────────────────────────────────
    # 5. Re-applying os.environ overrides secrets again
    # ──────────────────────────────────────────────────────────────
    os.environ["DB_HOST"] = "local-override.test"
    set_environment(os.environ)

    print("\n── after re-applying os.environ ──")
    snapshot = env()
    print(snapshot)
    assert snapshot.DB_HOST == "local-override.test"
    # DB_NAME still 'production' — os.environ didn't have DB_NAME
    assert snapshot.DB_NAME == "production"

    # ──────────────────────────────────────────────────────────────
    # 6. Custom converter in action
    # ──────────────────────────────────────────────────────────────
    # FEATURE_FLAG uses the to_boolean_string converter, so integer
    # and boolean inputs are normalised to "true" / "false".
    set_environment({"FEATURE_FLAG": 1})
    print("\n── custom converter (int → BooleanString) ──")
    print(f"FEATURE_FLAG = {env().FEATURE_FLAG!r}")
    assert env().FEATURE_FLAG == "true"

    set_environment({"FEATURE_FLAG": False})
    print(f"FEATURE_FLAG = {env().FEATURE_FLAG!r}")
    assert env().FEATURE_FLAG == "false"

    print("\n✅ All assertions passed.")


if __name__ == "__main__":
    main()
