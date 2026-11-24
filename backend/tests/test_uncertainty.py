from app.solvers.uncertainty import UncertaintyInput, solve


def test_pessimistic_picks_bing():
    r = solve(
        UncertaintyInput(
            alternatives=["甲", "乙", "丙"],
            states=["好", "差"],
            payoffs=[[20, 10], [18, 12], [15, 14]],
            sense="max",
            criterion="pessimistic",
        )
    )
    assert r.best == "丙"
    assert r.scores["丙"] == 14


def test_optimistic_picks_jia():
    r = solve(
        UncertaintyInput(
            alternatives=["甲", "乙", "丙"],
            states=["好", "差"],
            payoffs=[[20, 10], [18, 12], [15, 14]],
            sense="max",
            criterion="optimistic",
        )
    )
    assert r.best == "甲"
