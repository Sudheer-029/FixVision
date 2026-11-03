"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { postJson } from "@/lib/api";

export default function NewJob() {
  const router = useRouter();
  const [dataClass, setDataClass] = useState<"staged" | "customer">("staged");
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const body = {
        data_class: dataClass,
        ...(dataClass === "staged" && token ? { token: token.trim() } : {}),
      };
      const job = await postJson<{ id: string }>("/jobs", body);
      router.push(`/jobs/${job.id}`);
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }

  return (
    <main>
      <h1>FixVision</h1>
      <p className="tagline">See it. Fix it. Verify it.</p>
      <form onSubmit={(e) => void submit(e)} className="card stack">
        <h2>New job</h2>
        <p>
          <span className="field-label">Equipment</span>
          3–6 V mini submersible pump
        </p>
        <label>
          <span className="field-label">Data</span>
          <select
            value={dataClass}
            onChange={(e) => setDataClass(e.target.value as "staged" | "customer")}
          >
            <option value="staged">Staged test rig</option>
            <option value="customer">Customer job</option>
          </select>
        </label>
        {dataClass === "staged" && (
          <label>
            <span className="field-label">Code in a recorded clip (optional)</span>
            <input
              value={token}
              onChange={(e) => setToken(e.target.value)}
              maxLength={4}
              placeholder="Leave empty for a new code"
              autoCapitalize="characters"
              autoComplete="off"
            />
          </label>
        )}
        <button disabled={busy}>Start job</button>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </form>
    </main>
  );
}
