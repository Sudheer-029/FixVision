"""A fully healthy, passing job, plus helpers to break exactly one thing."""

from app.verification.schema import Conditions, JobEvidence, Observation, Thresholds, Timeline

TOKEN = "K7Q2"
FPS = 3
CLIP_S = 40.0
ON_T, OFF_T = 4.0, 34.0  # 30 s run
FILL_START, FILL_MARK = 8.0, 28.0  # 20 s = healthy speed

THRESHOLDS = Thresholds(version="test.1", baseline_fill_s=20.0)  # pass ≤ 25 s, fail > 33.3 s


def timeline(start: float = 0.0, end: float = CLIP_S) -> Timeline:
    """Mask present at every 3 fps sample in [start, end]."""
    k0, k1 = round(start * FPS), round(end * FPS)
    return Timeline(times=[k / FPS for k in range(k0, k1 + 1)], interval_s=1 / FPS)


def obs(id, value, clip="test", confidence=0.95, t=()) -> Observation:
    return Observation(id=id, clip=clip, value=value, confidence=confidence, t=list(t))


def healthy(fault: str = "F1", **overrides) -> JobEvidence:
    observations = [
        obs("job_token_read", TOKEN, t=[1.0]),
        obs("timer_visible", True),
        obs("pump_submerged", True),
        obs("switch_on_shown", True, t=[ON_T]),
        obs("switch_off_shown", True, t=[OFF_T]),
        obs("pump_running", True),
        obs("water_flowing", True, t=[ON_T + 0.5]),
        obs("fill_start_t", FILL_START, t=[FILL_START]),
        obs("fill_line_t", FILL_MARK, t=[FILL_MARK]),
        obs("leak_at_hose", False),
        obs("job_token_read", TOKEN, clip="closeup", t=[0.5]),
        obs("intake_clear", True, clip="closeup", t=[3.0]),
    ]
    data = dict(
        job_id="job-1",
        job_token=TOKEN,
        fault_hypothesis=fault,
        test_clip_duration_s=CLIP_S,
        observations=observations,
        equipment="mini_pump_3_6v",
        timelines={
            "test": {
                "jar": timeline(),
            },
            "closeup": {"intake": timeline(0.0, 5.0)},
        },
        fill_time_s=FILL_MARK - FILL_START,
        conditions=Conditions(supply="usb_5v", head_cm=20, water_level_cm=8),
    )
    data.update(overrides)
    return JobEvidence(**data)


def replace_obs(ev: JobEvidence, id: str, clip: str = "test", **fields) -> JobEvidence:
    """Change fields of one observation; pass `drop=True` to remove it."""
    out = []
    for o in ev.observations:
        if o.id == id and o.clip == clip:
            if fields.get("drop"):
                continue
            o = o.model_copy(update=fields)
        out.append(o)
    return ev.model_copy(update={"observations": out})


def with_timeline(ev: JobEvidence, concept: str, tl: Timeline | None) -> JobEvidence:
    clip = "closeup" if concept == "intake" else "test"
    clips = {**ev.timelines, clip: {**ev.timelines.get(clip, {}), concept: tl}}
    return ev.model_copy(update={"timelines": clips})
