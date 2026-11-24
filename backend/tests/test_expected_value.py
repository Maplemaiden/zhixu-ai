from app.solvers.expected_value import ExpectedValueInput, solve


def test_new_product_stocking():
    data = ExpectedValueInput(
        alternatives=["甲", "乙"],
        states=["旺季", "平季"],
        probs=[0.4, 0.6],
        payoffs=[[12, 4], [8, 6]],
        sense="max",
    )
    r = solve(data)
    assert r.expectations["甲"] == 7.2
    assert r.expectations["乙"] == 6.8
    assert r.best == "甲"


def test_prob_sum_error():
    data = ExpectedValueInput(
        alternatives=["A"],
        states=["s1", "s2"],
        probs=[0.3, 0.3],
        payoffs=[[1, 2]],
    )
    try:
        solve(data)
        assert False, "should raise"
    except ValueError as e:
        assert "概率之和" in str(e)
