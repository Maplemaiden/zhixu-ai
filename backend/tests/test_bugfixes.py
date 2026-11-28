import pytest
from fastapi import HTTPException

from app.routers.quiz import GradeBody, grade, list_questions
from app.routers.teach import AskBody, ChatTurn, ask
from app.services import lesson_reading, rag, user_db
from app.solvers.expected_value import ExpectedValueInput, solve as solve_ev
from app.solvers.madm import MadmInput, solve as solve_madm
from app.solvers.uncertainty import UncertaintyInput, solve as solve_uncertainty


def test_rag_home_preset_expected_value_hits_ch2():
    chunks = rag.load_chunks(force=True)
    assert all(not c["title"].startswith("#") and not c["title"].startswith("\ufeff") for c in chunks)
    hits = rag.retrieve("期望值准则怎么用？")
    assert hits, "RAG should return chunks"
    assert hits[0]["source"] == "期望值_第二讲.md"
    assert all(not h["title"].startswith("#") for h in hits)


def test_rag_natural_chinese_queries():
    rag.load_chunks(force=True)
    hits_cmp = rag.retrieve("风险型和不确定型怎么区分？")
    assert any("概述_第一讲" in h["source"] for h in hits_cmp)

    hits_ahp = rag.retrieve("AHP 适合什么问题？")
    assert hits_ahp and "AHP_第七讲.md" == hits_ahp[0]["source"]


def test_madm_weighted_product_zero_attribute_gives_exact_zero():
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
        interval={
            "生师比": {
                "best_low": 5,
                "best_high": 6,
                "tol_low": 2,
                "tol_high": 12,
            }
        },
    )
    res_nonzero_w = solve_madm(
        MadmInput(**payload, weights=[0.2, 0.05, 0.65, 0.1], method="weighted_product")
    )
    assert res_nonzero_w.scores["x5"] == 0.0

    res_zero_w = solve_madm(
        MadmInput(**payload, weights=[0.2, 0.0, 0.7, 0.1], method="weighted_product")
    )
    assert res_zero_w.scores["x5"] > 0.0


def test_lesson_reading_preserves_document_order():
    rag.load_chunks(force=True)
    data = lesson_reading.get_lesson_reading("expected_value")
    sections = data["sections"]
    assert len(sections) >= 2
    full_doc = (rag.get_settings().knowledge_dir / "期望值_第二讲.md").read_text(encoding="utf-8")
    positions = [full_doc.find(sec["title"]) for sec in sections]
    assert all(pos >= 0 for pos in positions)
    assert positions == sorted(positions), f"Expected ordered sections, got {positions}"


def test_quiz_hides_answers_and_blocks_traversal():
    data = list_questions("expected_value")
    assert data["count"] > 0
    for item in data["items"]:
        assert "answer" not in item
        assert "reason" not in item

    with pytest.raises(HTTPException) as exc:
        list_questions("..")
    assert exc.value.status_code == 400

    first_choice = next(x for x in data["items"] if x["type"] == "choice")
    first_opt = next(iter(first_choice["options"].keys()))
    graded = grade(GradeBody(question_id=first_choice["id"], method_id="expected_value", choice=first_opt))
    assert "answer" in graded
    assert "correct" in graded


def test_auth_password_length_and_display_name(tmp_path, monkeypatch):
    monkeypatch.setattr(user_db, "_db_path", lambda: tmp_path / "test_users.db")
    user_db.init_db()

    with pytest.raises(ValueError, match="密码至少 6 位"):
        user_db.register_user("alice", "12345")

    with pytest.raises(ValueError, match="密码不能全为空格"):
        user_db.register_user("alice", "      ")

    u = user_db.register_user("alice", "secret123", "   ")
    assert u["display_name"] == "alice"


def test_teach_ask_blank_rejected_and_history_accepted():
    with pytest.raises(HTTPException) as exc:
        ask(AskBody(question="   ", method_id="course"))
    assert exc.value.status_code == 400

    res = ask(
        AskBody(
            question="再举个例子",
            method_id="expected_value",
            history=[ChatTurn(role="user", text="期望值准则怎么用？")],
        )
    )
    assert "answer" in res
    assert len(res["sources"]) > 0


def test_madm_topsis_huge_value_does_not_overflow_column():
    """P2-6: 超大值 1e200 不得在向量规范化中溢出导致整列归零。"""
    res = solve_madm(
        MadmInput(
            alternatives=["x1", "x2", "x3"],
            attributes=["效益大数", "普通属性"],
            types=["benefit", "benefit"],
            matrix=[
                [1e200, 1.0],
                [5000.0, 10.0],
                [6000.0, 10.0],
            ],
            weights=[0.8, 0.2],
            method="topsis",
        )
    )
    z = res.steps[0]["values"]["Z"]
    assert z[0][0] == 1.0, f"Expected normalized huge value to be 1.0, got {z[0][0]}"
    assert res.best == "x1"
    assert res.all_equal is False


def test_madm_all_equal_matrix_reports_no_unique_best():
    """P2-7: 全部方案完全等价时不得宣布唯一最优方案。"""
    for method in ("topsis", "weighted_sum", "weighted_product"):
        res = solve_madm(
            MadmInput(
                alternatives=["x1", "x2", "x3", "x4", "x5"],
                attributes=["a1", "a2", "a3", "a4"],
                types=["benefit", "benefit", "benefit", "cost"],
                matrix=[[1, 1, 1, 1] for _ in range(5)],
                weights=[0.25, 0.25, 0.25, 0.25],
                method=method,
            )
        )
        assert res.all_equal is True
        assert res.best == ""
        assert "无差异" in res.panel_markdown


def test_ev_and_uncertainty_all_equal_reports_no_unique_best():
    ev_res = solve_ev(
        ExpectedValueInput(
            alternatives=["甲", "乙"],
            states=["好", "差"],
            probs=[0.5, 0.5],
            payoffs=[[10, 10], [10, 10]],
        )
    )
    assert ev_res.all_equal is True
    assert ev_res.best == ""

    unc_res = solve_uncertainty(
        UncertaintyInput(
            alternatives=["甲", "乙"],
            states=["好", "差"],
            payoffs=[[5, 5], [5, 5]],
            criterion="pessimistic",
        )
    )
    assert unc_res.all_equal is True
    assert unc_res.best == ""


def test_madm_and_uncertainty_signed_huge_values():
    """含正负超大值时 TOPSIS/加权和不溢出归零，不确定型溢出返回明确 ValueError。"""
    res_topsis = solve_madm(
        MadmInput(
            alternatives=["x1", "x2", "x3"],
            attributes=["a1", "a2"],
            types=["benefit", "cost"],
            matrix=[[1e200, 10.0], [-1e200, 5.0], [0.0, 1.0]],
            weights=[0.5, 0.5],
            method="topsis",
        )
    )
    assert res_topsis.best == "x1"
    assert res_topsis.scores["x1"] > res_topsis.scores["x2"]

    res_ws = solve_madm(
        MadmInput(
            alternatives=["x1", "x2"],
            attributes=["a1", "a2"],
            types=["benefit", "cost"],
            matrix=[[1e308, 10.0], [-1e308, 5.0]],
            weights=[0.6, 0.4],
            method="weighted_sum",
        )
    )
    assert res_ws.best == "x1"

    with pytest.raises(ValueError, match="溢出"):
        solve_uncertainty(
            UncertaintyInput(
                alternatives=["甲", "乙"],
                states=["好", "差"],
                payoffs=[[1e308, 1e308], [-1e308, -1e308]],
                criterion="regret",
            )
        )
