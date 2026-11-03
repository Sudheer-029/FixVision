"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, API_URL, type ServiceRecord } from "@/lib/api";
import { cleanReason, HEADLINE, RESULT_LABEL, SUPPLY_LABEL } from "@/lib/verdict";

const when = (iso: string) => new Date(iso).toLocaleString();
const seconds = (n: number | null) => (n === null ? "not recorded" : `${n} s`);

export default function RecordPage() {
  const { id } = useParams<{ id: string }>();
  const [rec, setRec] = useState<ServiceRecord | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<ServiceRecord>(`/jobs/${id}/record`).then(setRec, (e: Error) => setError(e.message));
  }, [id]);

  const c = rec?.conditions;
  return (
    <main>
      <h1>Service record</h1>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {rec && c && (
        <>
          <section className={`verdict ${rec.verdict.toLowerCase()}`}>
            <h2>{HEADLINE[rec.verdict]}</h2>
            {rec.reasons.map((r) => (
              <p key={r}>{cleanReason(r)}</p>
            ))}
          </section>

          <section className="card">
            <dl className="record">
              <dt>Job</dt>
              <dd>
                {rec.job_token} ({rec.job_id}){rec.data_class === "staged" && ", staged test rig"}
              </dd>
              <dt>Equipment</dt>
              <dd>3–6 V mini submersible pump</dd>
              <dt>Fault checked</dt>
              <dd>{rec.fault_hypothesis === "F1" ? "F1, blocked inlet" : "Out of scope"}</dd>
              {rec.symptom_transcript && (
                <>
                  <dt>Reported symptom</dt>
                  <dd lang="hi">{rec.symptom_transcript}</dd>
                </>
              )}
              <dt>Fill time</dt>
              <dd>
                {seconds(rec.measurements.fill_time_video_s)} from the video,{" "}
                {seconds(rec.measurements.fill_time_typed_s)} typed
              </dd>
              <dt>Run time</dt>
              <dd>{seconds(rec.measurements.run_s)}</dd>
              <dt>Test conditions</dt>
              <dd>
                {c.supply ? SUPPLY_LABEL[c.supply] : "supply not recorded"}, hose height{" "}
                {c.head_cm ?? "?"} cm, water level {c.water_level_cm ?? "?"} cm
              </dd>
              <dt>Guide sections used</dt>
              <dd>{rec.guide_sections.join(", ") || "None"}</dd>
              <dt>Models and thresholds</dt>
              <dd>
                {Object.values(rec.models).join(", ")}; thresholds {rec.thresholds_version ?? "none"}
              </dd>
              <dt>Times</dt>
              <dd>
                Opened {when(rec.created_at)}, verified {when(rec.verified_at)}
              </dd>
              <dt>Manager review</dt>
              <dd>
                {rec.review.decision
                  ? `${rec.review.decision}${rec.review.note ? `: ${rec.review.note}` : ""}, ${when(rec.review.reviewed_at!)}`
                  : "Waiting for review"}
              </dd>
            </dl>
          </section>

          <section className="card stack">
            <h3>Checks</h3>
            <ul className="checks">
              {rec.checks.map((check) => (
                <li key={check.id}>
                  <span className={`badge ${check.result}`}>
                    {RESULT_LABEL[check.result] ?? check.result}
                  </span>
                  <span>{check.detail}</span>
                </li>
              ))}
            </ul>
            {rec.uncertainties.map((u) => (
              <p key={u} className="muted">
                Uncertainty: {u}
              </p>
            ))}
            {rec.requested_actions.map((a) => (
              <p key={a} className="muted">
                Requested: {a}
              </p>
            ))}
          </section>

          {rec.evidence_frames.length > 0 && (
            <section className="card stack">
              <h3>Evidence</h3>
              {rec.evidence_frames.map((concept) => (
                <figure key={concept}>
                  {/* eslint-disable-next-line @next/next/no-img-element -- served by our API */}
                  <img
                    src={`${API_URL}/jobs/${id}/evidence/${concept}`}
                    alt={`Video frame with the box SAM 3.1 found around the ${concept}`}
                  />
                  <figcaption>SAM 3.1 box: {concept}</figcaption>
                </figure>
              ))}
            </section>
          )}

          <div className="stack no-print">
            <button className="secondary" onClick={() => window.print()}>
              Print or save as PDF
            </button>
            <a
              className="button secondary"
              href={`${API_URL}/jobs/${id}/record`}
              download={`fixvision-${rec.job_token}.json`}
            >
              Download JSON
            </a>
          </div>
        </>
      )}
      <nav className="links">
        <Link href={`/jobs/${id}`}>Back to the job</Link>
      </nav>
    </main>
  );
}
