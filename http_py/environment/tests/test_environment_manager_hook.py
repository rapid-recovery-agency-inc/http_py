from dataclasses import replace, dataclass

from http_py.environment import create_environment


@dataclass(frozen=True)
class Env:
    A: int = 0
    B: int = 0


@dataclass(frozen=True)
class PreferEnv:
    A: int | None = None
    B: int | None = None


def increment_a(env: Env) -> Env:
    return replace(env, A=env.A + 1)


def test_post_set_hook_modifies_state() -> None:
    mgr = create_environment(Env, post_set_hook=increment_a)
    mgr.set_environment({"A": 2, "B": 3})
    result = mgr.env()
    assert result.A == 3
    assert result.B == 3


def test_post_set_hook_chain() -> None:
    def double_b(env: Env) -> Env:
        return replace(env, B=env.B * 2)

    mgr = create_environment(Env, post_set_hook=lambda d: double_b(increment_a(d)))
    mgr.set_environment({"A": 1, "B": 2})
    result = mgr.env()
    assert result.A == 2
    assert result.B == 4


def test_set_environment_prefer_set_values_empty_state_flag_off() -> None:
    mgr = create_environment(PreferEnv)

    mgr.set_environment({"A": 1, "B": 2}, prefer_set_values=False)

    result = mgr.env()
    assert result.A == 1
    assert result.B == 2


def test_set_environment_prefer_set_values_non_empty_state_no_conflicts_flag_off() -> (
    None
):
    mgr = create_environment(PreferEnv)

    # Seed A; B starts as None (raw None values are ignored by coercion).
    mgr.set_environment({"A": 1}, prefer_set_values=True)

    # Fill missing field(s) without overwriting existing non-None values.
    mgr.set_environment({"B": 3}, prefer_set_values=False)

    result = mgr.env()
    assert result.A == 1
    assert result.B == 3


def test_set_environment_prefer_set_values_non_empty_state_conflicts_flag_off() -> None:
    mgr = create_environment(PreferEnv)

    mgr.set_environment({"A": 1, "B": 2}, prefer_set_values=False)
    mgr.set_environment({"A": 10, "B": 20}, prefer_set_values=False)

    result = mgr.env()
    assert result.A == 10
    assert result.B == 20


def test_set_environment_prefer_set_values_non_empty_state_conflicts_flag_on() -> None:
    mgr = create_environment(PreferEnv)

    # Seed A; B starts as None (raw None values are ignored by coercion).
    mgr.set_environment({"A": 1}, prefer_set_values=True)

    # A is a conflict but should be preserved since it's non-None already.
    # B should be replaced since it's currently None.
    mgr.set_environment({"A": 10, "B": 5}, prefer_set_values=True)

    result = mgr.env()
    assert result.A == 1
    assert result.B == 5
