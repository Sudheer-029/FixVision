"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Capture } from "@/components/Capture";
import { postJson, uploadMedia, type Guidance, type Job, type Triage } from "@/lib/api";
import { isBusy, useJob } from "@/lib/useJob";

type ScreenProps = { job: Job; refresh: () => Promise<void> };

const WORKING: Record<string, string> = {
  triage: "Muse Spark is reading the symptom…",
  guidance: "Muse Spark is preparing guidance from the pump guide…",
  verify: "SAM 3.1 and Muse Spark are checking the videos. This can take a few minutes…",
};

/** The step that failed while the job was in the state it is in now. */
const RETRY_STATE: Record<string, string> = {
  triage: "SYMPTOM_CAPTURED",
  guidance: "CHECK_CAPTURED",
  verify: "VERIFYING",
};

function stepResult<T>(job: Job, name: string): T | null {
  const step = job.steps.find((s) => s.step.split(":")[0] === name && s.status === "done");
  return (step?.result as T | undefined) ?? null;
}

function useSubmit(refresh: () => Promise<void>) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function run(fn: () => Promise<unknown>) {
    setBusy(true);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    }
    await refresh();
    setBusy(false);
  }
  return { busy, error, run };
}

function Problem({ text }: { text: string }) {
  return text ? (
    <p className="error" role="alert">
      {text}
    </p>
  ) : null;
}

function Symptom({ job, refresh }: ScreenProps) {
  const [file, setFile] = useState<File | null>(null);
  const [transcript, setTranscript] = useState("");
  const { busy, error, run } = useSubmit(refresh);
  const needsClip = job.state === "CREATED";

  return (
    <section className="card stack">
      <h2>1. Show the problem</h2>
      {needsClip && (
        <Capture label="Short video of the pump (up to 30 s)" file={file} onFile={setFile} />
      )}
      <label>
        <span className="field-label">What is wrong?</span>
        <textarea
          rows={3}
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          placeholder="For example: water comes out slowly"
        />
      </label>
      <button
        disabled={busy || (needsClip && !file)}
        onClick={() =>
          void run(async () => {
            if (needsClip) await uploadMedia(job.id, "symptom", file!);
            await postJson(`/jobs/${job.id}/triage`, { transcript });
          })
        }
      >
        {busy ? "Sending…" : "Find likely causes"}
      </button>
      <Problem text={error} />
    </section>
  );
}

function CheckCapture({ job, refresh }: ScreenProps) {
  const [file, setFile] = useState<File | null>(null);
  const { busy, error, run } = useSubmit(refresh);
  const triage = stepResult<Triage>(job, "triage");

  return (
    <section className="card stack">
      <h2>2. Run this check</h2>
      <p className="instruction">{triage?.requested_check.instruction}</p>
      <Capture label="Video of the check" file={file} onFile={setFile} />
      <button
        disabled={busy || !file}
        onClick={() => void run(() => uploadMedia(job.id, "check", file!))}
      >
        {busy ? "Uploading…" : "Upload check"}
      </button>
      <Problem text={error} />
    </section>
  );
}

function ConfirmCause({ job, refresh }: ScreenProps) {
  const { busy, error, run } = useSubmit(refresh);
  const triage = stepResult<Triage>(job, "triage");

  return (
    <section className="card stack">
      <h2>3. Confirm the cause</h2>
      {triage?.causes.map((cause) => (
        <div key={cause.fault_id} className="cause">
          <h3>
            {cause.fault_id === "F1" ? "Blocked inlet" : "Something else"}{" "}
            <small>{Math.round(cause.likelihood * 100)}% likely</small>
          </h3>
          <ul>
            {cause.evidence.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <button
            className="secondary"
            disabled={busy}
            onClick={() =>
              void run(() => postJson(`/jobs/${job.id}/guidance`, { fault_id: cause.fault_id }))
            }
          >
            Confirm this cause
          </button>
        </div>
      ))}
      <Problem text={error} />
    </section>
  );
}

function RepairGuidance({ job, refresh }: ScreenProps) {
  const guidance = stepResult<Guidance>(job, "guidance");
  // shortcut: approvals live in this page only, store them with the job for the T9 service record
  const [approved, setApproved] = useState<Record<number, boolean>>({});
  const [stopped, setStopped] = useState(false);
  const allApproved = guidance?.steps.every((s, i) => !s.requires_approval || approved[i]) ?? false;

  if (stopped) {
    return (
      <section className="card stack">
        <h2>Repair stopped</h2>
        <p>Leave the pump switched off and pass this job to a senior technician.</p>
        <button className="secondary" onClick={() => setStopped(false)}>
          Back to the guidance
        </button>
      </section>
    );
  }

  return (
    <section className="card stack">
      <h2>4. Repair</h2>
      <div className="stop-box">
        <h3>Stop if</h3>
        <ul>
          {guidance?.stop_conditions.map((c) => (
            <li key={c}>{c}</li>
          ))}
        </ul>
      </div>
      <ol className="steps">
        {guidance?.steps.map((s, i) => (
          <li key={s.text}>
            <p>{s.text}</p>
            {s.requires_approval && (
              <label className="check">
                <input
                  type="checkbox"
                  checked={approved[i] ?? false}
                  onChange={(e) => setApproved({ ...approved, [i]: e.target.checked })}
                />
                I approve this step
              </label>
            )}
          </li>
        ))}
      </ol>
      <p className="muted">From the pump guide: {guidance?.cited_sections.join(", ")}</p>
      <button className="danger" onClick={() => setStopped(true)}>
        Stop the repair
      </button>
      {allApproved ? (
        <Closeup job={job} refresh={refresh} title="After the repair" />
      ) : (
        <p className="muted">Approve each step to continue.</p>
      )}
    </section>
  );
}

function Closeup({ job, refresh, title }: ScreenProps & { title: string }) {
  const [file, setFile] = useState<File | null>(null);
  const { busy, error, run } = useSubmit(refresh);

  return (
    <div className="stack">
      <h3>{title}</h3>
      <p>Film up to 10 s: first the job code, then the clean intake, close up.</p>
      <Capture label="Close-up video" file={file} onFile={setFile} />
      <button
        disabled={busy || !file}
        onClick={() => void run(() => uploadMedia(job.id, "closeup", file!))}
      >
        {busy ? "Uploading…" : "Upload close-up"}
      </button>
      <Problem text={error} />
    </div>
  );
}

const MIN_RUN_S = 20;

function TestChecklist({ token, seconds }: { token: string; seconds: number }) {
  return (
    <ul className="checklist">
      <li>
        Code <strong>{token}</strong>, running stopwatch and submerged pump in view
      </li>
      <li>Switch the pump on in view</li>
      <li className={seconds >= MIN_RUN_S ? "done" : ""}>Run at least {MIN_RUN_S} s</li>
      <li>Keep the hose and jar in frame until the water passes the line</li>
      <li>Switch the pump off in view, then stop recording</li>
    </ul>
  );
}

function FunctionalTest({ job, refresh }: ScreenProps) {
  const [file, setFile] = useState<File | null>(null);
  const [fill, setFill] = useState("");
  const [supply, setSupply] = useState("battery_9v");
  const [head, setHead] = useState("");
  const [level, setLevel] = useState("");
  const { busy, error, run } = useSubmit(refresh);
  const needsClip = job.state === "CLOSEUP_CAPTURED";

  function submit(e: FormEvent) {
    e.preventDefault();
    void run(async () => {
      if (file) await uploadMedia(job.id, "test", file);
      await postJson(`/jobs/${job.id}/test`, {
        fill_time_s: Number(fill),
        conditions: { supply, head_cm: Number(head), water_level_cm: Number(level) },
      });
    });
  }

  return (
    <form className="card stack" onSubmit={submit}>
      <h2>5. Functional test</h2>
      <TestChecklist token={job.token} seconds={0} />
      {job.state !== "VERIFYING" && (
        <Capture
          label="Test video"
          file={file}
          onFile={setFile}
          guide={(seconds) => <TestChecklist token={job.token} seconds={seconds} />}
        />
      )}
      <label>
        <span className="field-label">Time to fill to the line (s)</span>
        <input
          type="number"
          inputMode="decimal"
          min="0.1"
          max="600"
          step="0.1"
          required
          value={fill}
          onChange={(e) => setFill(e.target.value)}
        />
      </label>
      <label>
        <span className="field-label">Power supply</span>
        <select value={supply} onChange={(e) => setSupply(e.target.value)}>
          <option value="battery_9v">9 V battery</option>
          <option value="usb_5v">5 V USB</option>
        </select>
      </label>
      <label>
        <span className="field-label">Hose height (cm)</span>
        <input
          type="number"
          inputMode="decimal"
          min="0"
          step="0.5"
          required
          value={head}
          onChange={(e) => setHead(e.target.value)}
        />
      </label>
      <label>
        <span className="field-label">Water level (cm)</span>
        <input
          type="number"
          inputMode="decimal"
          min="0"
          step="0.5"
          required
          value={level}
          onChange={(e) => setLevel(e.target.value)}
        />
      </label>
      <button disabled={busy || (needsClip && !file)}>
        {busy ? "Sending…" : "Upload and verify"}
      </button>
      <Problem text={error} />
    </form>
  );
}

const HEADLINE = {
  PASSED: "Passed these checks under these conditions",
  FAILED: "Failed",
  INCONCLUSIVE: "Inconclusive: not enough evidence to decide",
};
const RESULT_LABEL: Record<string, string> = {
  pass: "Pass",
  fail: "Fail",
  insufficient_evidence: "Not enough evidence",
};
const SUPPLY_LABEL: Record<string, string> = { battery_9v: "9 V battery", usb_5v: "5 V USB" };

function VerdictScreen({ job, refresh }: ScreenProps) {
  const [again, setAgain] = useState(false);
  const verdict = job.verdict;
  if (!verdict) return null;
  const c = verdict.conditions;
  const canRetest = job.state === "FAILED" || job.state === "INCONCLUSIVE";

  return (
    <>
      <section className={`verdict ${verdict.verdict.toLowerCase()}`} role="status">
        <h2>{HEADLINE[verdict.verdict]}</h2>
        {verdict.reasons.map((r) => (
          <p key={r}>{r.replace(/^C\d_\w+: /, "")}</p>
        ))}
      </section>

      {verdict.requested_actions.length > 0 && (
        <section className="card stack">
          <h3>What to do next</h3>
          <ul>
            {verdict.requested_actions.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="card stack">
        <h3>Checks</h3>
        <ul className="checks">
          {verdict.checks.map((check) => (
            <li key={check.id}>
              <span className={`badge ${check.result}`}>
                {RESULT_LABEL[check.result] ?? check.result}
              </span>
              <span>{check.detail}</span>
            </li>
          ))}
        </ul>
        <p className="muted">
          Conditions: {c.supply ? SUPPLY_LABEL[c.supply] : "supply not recorded"}, hose height{" "}
          {c.head_cm ?? "?"} cm, water level {c.water_level_cm ?? "?"} cm
          {verdict.run_s !== null && `, run ${verdict.run_s} s`}.
        </p>
        {verdict.uncertainties.map((u) => (
          <p key={u} className="muted">
            Uncertainty: {u}
          </p>
        ))}
      </section>

      {job.evidence.length > 0 && (
        <section className="card stack">
          <h3>Evidence</h3>
          {job.evidence.map((concept) => (
            <figure key={concept}>
              {/* eslint-disable-next-line @next/next/no-img-element -- served by our API */}
              <img
                src={`/api/jobs/${job.id}/evidence/${concept}`}
                alt={`Video frame with the box SAM 3.1 found around the ${concept}`}
              />
              <figcaption>SAM 3.1 box: {concept}</figcaption>
            </figure>
          ))}
        </section>
      )}

      {job.record?.review && (
        <section className="card">
          <p>
            Manager {job.record.review} this record.{job.record.note && ` “${job.record.note}”`}
          </p>
        </section>
      )}

      <div className="stack">
        {canRetest &&
          (again ? (
            <section className="card">
              <Closeup job={job} refresh={refresh} title="Record again" />
            </section>
          ) : (
            <button className="secondary" onClick={() => setAgain(true)}>
              Repair or record again
            </button>
          ))}
        {job.state !== "REVIEWED" && (
          <Link className="button secondary" href={`/jobs/${job.id}/review`}>
            Manager review
          </Link>
        )}
      </div>
    </>
  );
}

function Screen({ job, refresh }: ScreenProps) {
  if (job.verdict && job.state !== "VERIFYING" && job.state !== "CLOSEUP_CAPTURED" && job.state !== "TEST_CAPTURED") {
    return <VerdictScreen job={job} refresh={refresh} />;
  }
  switch (job.state) {
    case "CREATED":
    case "SYMPTOM_CAPTURED":
      return <Symptom job={job} refresh={refresh} />;
    case "CHECK_REQUESTED":
      return <CheckCapture job={job} refresh={refresh} />;
    case "CHECK_CAPTURED":
      return <ConfirmCause job={job} refresh={refresh} />;
    case "GUIDANCE_ISSUED":
      return <RepairGuidance job={job} refresh={refresh} />;
    default:
      return <FunctionalTest job={job} refresh={refresh} />;
  }
}

export default function JobPage() {
  const { id } = useParams<{ id: string }>();
  const { job, error, refresh } = useJob(id);

  if (!job) {
    return (
      <main>
        {error ? <Problem text={error} /> : <p role="status">Loading…</p>}
      </main>
    );
  }

  const running = job.steps.find((s) => s.status === "queued" || s.status === "running");
  const failed = job.steps.find(
    (s) => s.status === "error" && RETRY_STATE[s.step.split(":")[0]] === job.state,
  );

  return (
    <main>
      <header className="job-head">
        <div>
          <span className="field-label">Job code</span>
          <p className="token" data-testid="token">
            {job.token}
          </p>
          <p className="muted">Keep this code in view in every video.</p>
        </div>
        {job.data_class === "staged" && <span className="pill">Staged test rig</span>}
      </header>

      {isBusy(job) && running ? (
        <section className="card working" role="status">
          <span className="spinner" aria-hidden="true" />
          <p>{WORKING[running.step.split(":")[0]]}</p>
        </section>
      ) : (
        <>
          {failed && (
            <p className="error" role="alert">
              That step failed ({failed.error}). Your videos are saved, so you can try again.
            </p>
          )}
          <Screen job={job} refresh={refresh} />
        </>
      )}

      <nav className="links">
        <Link href={`/jobs/${job.id}/trace`}>Model calls and cost</Link>
        <Link href="/">New job</Link>
      </nav>
    </main>
  );
}

