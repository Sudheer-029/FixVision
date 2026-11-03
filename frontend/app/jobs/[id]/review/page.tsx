"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { postJson } from "@/lib/api";
import { useJob } from "@/lib/useJob";
import { cleanReason } from "@/lib/verdict";

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { job, error: loadError } = useJob(id);
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function decide(approved: boolean) {
    setBusy(true);
    setError("");
    try {
      await postJson(`/jobs/${id}/review`, { approved, note });
      router.push(`/jobs/${id}`);
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }

  const problem = error || loadError;
  return (
    <main>
      <h1>Manager review</h1>
      {job?.verdict && (
        <section className="card stack">
          <p>
            Job <strong>{job.token}</strong>: {job.verdict.verdict}
          </p>
          {job.verdict.reasons.map((r) => (
            <p key={r} className="muted">
              {cleanReason(r)}
            </p>
          ))}
          <label>
            <span className="field-label">Note</span>
            <textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} />
          </label>
          <button disabled={busy} onClick={() => void decide(true)}>
            Approve record
          </button>
          <button className="danger" disabled={busy} onClick={() => void decide(false)}>
            Reject record
          </button>
        </section>
      )}
      {problem && (
        <p className="error" role="alert">
          {problem}
        </p>
      )}
      <nav className="links">
        <Link href={`/jobs/${id}`}>Back to the job</Link>
      </nav>
    </main>
  );
}
