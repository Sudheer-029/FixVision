"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type Job } from "./api";

const POLL_MS = 2000;

export function isBusy(job: Job) {
  return job.steps.some((s) => s.status === "queued" || s.status === "running");
}

/** The job, refreshed while the worker has something running. */
export function useJob(id: string) {
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      setJob(await api<Job>(`/jobs/${id}`));
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }, [id]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const busy = job !== null && isBusy(job);
  useEffect(() => {
    if (!busy) return;
    const timer = setInterval(() => void refresh(), POLL_MS);
    return () => clearInterval(timer);
  }, [busy, refresh]);

  return { job, error, refresh };
}
