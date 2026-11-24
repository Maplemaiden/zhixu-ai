from app.services.classify import ALLOWED, _parse


def test_parse_json_object():
    data = _parse('{"in_course": false, "method_id": null, "reason": "古诗", "confidence": "high"}')
    assert data["in_course"] is False
    assert data["method_id"] is None


def test_parse_fenced_json():
    data = _parse('```json\n{"in_course": true, "method_id": "bayes"}\n```')
    assert data["method_id"] == "bayes"


def test_allowed_methods_include_all_ready_topics():
    assert "decision_overview" in ALLOWED
    assert "expected_value" in ALLOWED
    assert "ahp" in ALLOWED
    assert "dea" in ALLOWED
    assert "goal_programming" in ALLOWED
    assert "utility_combine" in ALLOWED
    assert "markov" in ALLOWED
    assert "discrete_sim" in ALLOWED
    assert "madm" in ALLOWED
    assert len(ALLOWED) >= 20
    assert "madm9_prep" in ALLOWED
    assert "overview_elements" in ALLOWED
