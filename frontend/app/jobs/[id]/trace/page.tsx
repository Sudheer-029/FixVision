"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type Trace } from "@/lib/api";

const usd = (n: number) => `$${n.toFixed(4)}`;

export default function TracePage() {
  const { id } = useParams<{ id: string }>();
  const [trace, setTrace] = useState<Trace | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Trace>(`/jobs/${id}/trace`).then(setTrace, (e: Error) => setError(e.message));
  }, [id]);

  return (
    <main>
      <h1>Model calls and cost</h1>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {trace && (
        <>
          <p className="total">
            {trace.total_calls} calls, {usd(trace.total_cost_usd)}
          </p>
          {trace.steps.map((step) => (
            <section key={step.step} className="card stack">
              <h2>{step.step}</h2>
              <p className="muted">
                {step.status}, {(step.latency_ms / 1000).toFixed(1)} s, {usd(step.cost_usd)}
              </p>
              {step.error && <p className="error">{step.error}</p>}
              <ul className="calls">
                {step.calls.map((call) => (
                  <li key={`${call.ts}-${call.component}`}>
                    <span>
                      {call.component} <small>{call.model}</small>
                    </span>
                    <span>
                      {call.cached ? "cached" : `${((call.latency_ms ?? 0) / 1000).toFixed(1)} s`},{" "}
                      {usd(call.cost_usd)}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </>
      )}
      <nav className="links">
        <Link href={`/jobs/${id}`}>Back to the job</Link>
      </nav>
    </main>
  );
}
