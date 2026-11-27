from app.solvers.madm import MadmInput, solve


def _tiny():
    return MadmInput(
        alternatives=["甲", "乙"],
        attributes=["效益", "成本"],
        types=["benefit", "cost"],
        matrix=[[3, 4], [4, 3]],
        weights=[0.5, 0.5],
        method="topsis",
    )


def test_topsis_two_alt_hand():
    r = solve(_tiny())
    assert r.best == "乙"
    assert r.scores["乙"] == 1.0
    assert r.scores["甲"] == 0.0
    assert r.ranking == ["乙", "甲"]


def test_weighted_sum_two_alt():
    data = _tiny()
    data.method = "weighted_sum"
    r = solve(data)
    assert r.best == "乙"
    assert r.scores["乙"] == 1.0
    assert r.scores["甲"] == 0.0


def test_weighted_product_two_alt():
    data = _tiny()
    data.method = "weighted_product"
    r = solve(data)
    assert r.best == "乙"
    assert r.scores["乙"] > r.scores["甲"]


def test_weight_sum_error():
    try:
        solve(
            MadmInput(
                alternatives=["A"],
                attributes=["x", "y"],
                types=["benefit", "benefit"],
                matrix=[[1, 2]],
                weights=[0.2, 0.2],
            )
        )
        assert False, "should raise"
    except ValueError as e:
        assert "权重之和" in str(e)


def test_interval_maps_to_one_inside_best():
    r = solve(
        MadmInput(
            alternatives=["A", "B"],
            attributes=["生师比", "经费"],
            types=["interval", "benefit"],
            matrix=[[5.5, 10], [2, 10]],
            weights=[0.5, 0.5],
            method="weighted_sum",
            interval={
                "生师比": {
                    "best_low": 5,
                    "best_high": 6,
                    "tol_low": 2,
                    "tol_high": 12,
                }
            },
        )
    )
    # A 生师比在最优区间内得 1，B 落在容忍下限上得 0
    assert r.best == "A"


def test_methods_can_disagree_on_school_table():
    payload = dict(
        alternatives=["x1", "x2", "x3", "x4", "x5"],
        attributes=["人均专著", "生师比", "科研经费", "逾期毕业率"],
        types=["benefit", "interval", "benefit", "cost"],
        matrix=[
            [0.1, 5, 5000, 4.7],
            [0.2, 6, 6000, 5.6],
            [0.4, 7, 7000, 6.7],
            [0.9, 10, 10000, 2.3],
            [1.2, 2, 400, 1.8],
        ],
        weights=[0.2, 0.3, 0.4, 0.1],
        interval={
            "生师比": {
                "best_low": 5,
                "best_high": 6,
                "tol_low": 2,
                "tol_high": 12,
            }
        },
    )
    topsis = solve(MadmInput(**payload, method="topsis"))
    wsum = solve(MadmInput(**payload, method="weighted_sum"))
    assert topsis.best
    assert wsum.best
    assert len(topsis.ranking) == 5
    # 换方法至少得分表齐全；排序允许相同，但不能崩
    assert set(topsis.scores) == set(payload["alternatives"])
