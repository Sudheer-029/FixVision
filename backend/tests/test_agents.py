"""Reasoning agent on recorded Muse Spark answers (tests/fixtures/agents/, real rig clips)."""

import json
from pathlib import Path

import pytest

from app.agents import reasoning as R
from app.clients.meta_client import CallResult

FIX = Path(__file__).parent / "fixtures" / "agents"
VERDICT_WORDS = ("PASSED", "FAILED", "INCONCLUSIVE")


def golden(name: str) -> str:
    return (FIX / name).read_text()


class FakeClient:
    """Answers each respond() call with the next scripted text; records what was sent."""

    def __init__(self, *answers: str):
        self.answers, self.sent = list(answers), []

    def respond(self, model, input, schema=None, **_):
        self.sent.append(input)
        return CallResult(text=self.answers.pop(0))

    def upload_file(self, path):
        return "file-123"


def sent_text(client: FakeClient) -> str:
    return json.dumps(client.sent)


def test_observe_test_returns_exactly_the_spec_ids():
    client = FakeClient(golden("observe_test_healthy_01.json"))
    obs = R.observe_test(client, "m", "clip.mp4", "test")
    assert [o.id for o in obs] == list(R.TEST_OBS)
    by_id = {o.id: o for o in obs}
    assert by_id["job_token_read"].value == "K7M4"
    assert by_id["switch_on_shown"].value is True and by_id["switch_on_shown"].t
    assert by_id["water_flowing"].value is True
    assert all(o.clip == "test" and 0 <= o.confidence <= 1 for o in obs)


def test_closeup_asks_only_closeup_ids():
    answer = json.dumps(
        {
            "job_token_read": {"value": "R2C6", "confidence": 0.9, "t": [0.5]},
            "intake_clear": {"value": True, "confidence": 1.4, "t": [6.0]},
        }
    )
    obs = R.observe_test(FakeClient(answer), "m", "closeup.mp4", "closeup")
    assert [(o.id, o.clip) for o in obs] == [
        ("job_token_read", "closeup"),
        ("intake_clear", "closeup"),
    ]
    assert obs[1].confidence == 1.0  # uncalibrated confidence is clamped


def test_prompts_never_carry_a_verdict_or_the_token():
    client = FakeClient(golden("observe_test_healthy_01.json"))
    R.observe_test(client, "m", "clip.mp4", "test")
    text = sent_text(client)
    assert "K7M4" not in text  # the token is read from the video, never sent
    for word in VERDICT_WORDS:
        assert word not in text


def test_schema_failure_gets_one_repair():
    good = golden("observe_test_healthy_01.json")
    client = FakeClient('{"job_token_read": "oops"}', good)
    assert len(R.observe_test(client, "m", "clip.mp4", "test")) == len(R.TEST_OBS)
    assert "did not match the JSON schema" in sent_text(client)


def test_second_schema_failure_is_an_error():
    client = FakeClient("not json", "still not json")
    with pytest.raises(R.AgentError):
        R.observe_test(client, "m", "clip.mp4", "test")


# -- observe_fill ------------------------------------------------------------------


def test_golden_fill_labels_give_fill_times(tmp_path):
    frames = [tmp_path / f"f{i:04d}.jpg" for i in range(35)]
    for f in frames:
        f.write_bytes(b"\xff\xd8")
    obs = R.observe_fill(FakeClient(golden("observe_fill_healthy_01.json")), "m", frames)
    start, line = obs
    assert (start.id, start.value) == ("fill_start_t", 2.0)
    assert (line.id, line.value) == ("fill_line_t", 28.0)
    assert start.confidence == line.confidence == R.FILL_CONFIDENCE


def test_wrong_label_count_is_repaired(tmp_path):
    frames = [tmp_path / f"f{i}.jpg" for i in range(3)]
    for f in frames:
        f.write_bytes(b"\xff\xd8")
    two = json.dumps({"frames": ["not_filling", "below_line"]})
    three = json.dumps({"frames": ["not_filling", "below_line", "at_line"]})
    client = FakeClient(two, three)
    assert R.observe_fill(client, "m", frames)[1].value == 2.0
    assert "expected 3 labels, got 2" in sent_text(client)


@pytest.mark.parametrize(
    "labels, start, line, conf",
    [
        (["not_filling", "below_line", "below_line", "at_line"], 1.0, 3.0, R.FILL_CONFIDENCE),
        (["below_line", "below_line"], 0.0, None, R.FILL_CONFIDENCE),  # never reached the line
        (["not_filling", "not_filling"], None, None, R.FILL_CONFIDENCE),
        (["below_line", "at_line", "below_line", "at_line"], 0.0, 1.0, R.FILL_JUMBLED),
    ],
)
def test_fill_times(labels, start, line, conf):
    s, ln = R.fill_times(labels, fps=1.0)
    assert (s.value, ln.value, s.confidence) == (start, line, conf)
    assert ln.t == ([] if line is None else [line])


def test_jumbled_labels_fall_below_the_confidence_threshold():
    assert R.FILL_JUMBLED < 0.7 <= R.FILL_CONFIDENCE


# -- triage and guidance ----------------------------------------------------------------


def test_triage_golden():
    client = FakeClient(golden("triage_slow_fill.json"))
    t = R.triage(client, "m", None, "paani dheere aa raha hai")
    assert t.causes[0].fault_id == "F1" and t.causes[0].evidence
    assert t.requested_check.instruction
    assert "G-F1" in sent_text(client)  # the approved guide is in the prompt


def test_guidance_golden_cites_the_guide():
    g = R.guidance(FakeClient(golden("guidance_f1.json")), "m", "F1")
    assert set(g.cited_sections) <= {"G-F1", "G-SAFETY"} and g.cited_sections
    assert any(s.requires_approval for s in g.steps) and g.stop_conditions


def test_guidance_citing_unknown_section_is_repaired():
    bad = json.loads(golden("guidance_f1.json")) | {"cited_sections": ["G-F9"]}
    client = FakeClient(json.dumps(bad), golden("guidance_f1.json"))
    assert R.guidance(client, "m", "F1").cited_sections != ["G-F9"]
    assert "cited_sections must be guide section ids" in sent_text(client)


def test_every_prompt_has_an_id():
    for path in R.PROMPTS.glob("*.md"):
        assert R.prompt_id(path.read_text()).startswith(f"{path.stem}.v")
