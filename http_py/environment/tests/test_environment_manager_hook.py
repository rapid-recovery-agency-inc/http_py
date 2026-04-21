from dataclasses import replace, dataclass

from http_py.environment import create_environment


@dataclass(frozen=True)
class Env:
    A: int = 0
    B: int = 0


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
