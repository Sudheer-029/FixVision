"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

type Props = {
  label: string;
  file: File | null;
  onFile: (file: File | null) => void;
  /** Shown while recording; gets the seconds recorded so far. */
  guide?: (seconds: number) => ReactNode;
  audioOnly?: boolean;
};

function canRecord() {
  return (
    typeof MediaRecorder !== "undefined" && typeof navigator.mediaDevices?.getUserMedia === "function"
  );
}

/** Records in the browser where it can; a file input is always there (and the only way on HTTP). */
export function Capture({ label, file, onFile, guide, audioOnly = false }: Props) {
  const [supported, setSupported] = useState(false);
  const [seconds, setSeconds] = useState<number | null>(null);
  const [problem, setProblem] = useState("");
  const video = useRef<HTMLVideoElement>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);

  useEffect(() => {
    setSupported(canRecord());
    return () => stream.current?.getTracks().forEach((t) => t.stop());
  }, []);

  const recording = seconds !== null;
  useEffect(() => {
    if (!recording) return;
    const timer = setInterval(() => setSeconds((s) => (s ?? 0) + 1), 1000);
    return () => clearInterval(timer);
  }, [recording]);

  async function start() {
    setProblem("");
    try {
      const media = await navigator.mediaDevices.getUserMedia(
        audioOnly ? { audio: true } : { video: { facingMode: "environment" }, audio: true },
      );
      stream.current = media;
      const base = audioOnly ? "audio" : "video";
      const type = MediaRecorder.isTypeSupported(`${base}/mp4`) ? `${base}/mp4` : `${base}/webm`;
      const rec = new MediaRecorder(media, { mimeType: type });
      const chunks: Blob[] = [];
      rec.ondataavailable = (e) => chunks.push(e.data);
      rec.onstop = () => {
        media.getTracks().forEach((t) => t.stop());
        const ext = type.endsWith("mp4") ? "mp4" : "webm";
        onFile(new File(chunks, `clip.${ext}`, { type }));
      };
      recorder.current = rec;
      rec.start();
      setSeconds(0);
      onFile(null);
      // the <video> element mounts with the recording state
      requestAnimationFrame(() => {
        if (video.current) video.current.srcObject = media;
      });
    } catch {
      setProblem("Recording is not available here. Choose a file instead.");
    }
  }

  function stop() {
    recorder.current?.stop();
    setSeconds(null);
  }

  return (
    <div className="capture">
      <p className="field-label">{label}</p>
      {recording ? (
        <>
          {!audioOnly && <video ref={video} className="preview" autoPlay muted playsInline />}
          <p className="timer" role="timer">
            {seconds} s
          </p>
          {guide?.(seconds)}
          <button type="button" className="danger" onClick={stop}>
            Stop recording
          </button>
        </>
      ) : (
        <div className="capture-actions">
          {supported && (
            <button type="button" className="secondary" onClick={() => void start()}>
              {audioOnly ? "Record voice" : "Record video"}
            </button>
          )}
          <label className="file">
            {audioOnly ? "Choose an audio file" : "Choose a video file"}
            <input
              type="file"
              aria-label={audioOnly ? "Audio file" : "Video file"}
              accept={audioOnly ? "audio/*,.m4a,.wav,.webm,.mp4" : "video/*,.mov,.mp4,.webm"}
              onChange={(e) => onFile(e.target.files?.[0] ?? null)}
            />
          </label>
        </div>
      )}
      {file && <p className="ok">Ready: {file.name}</p>}
      {problem && (
        <p className="error" role="alert">
          {problem}
        </p>
      )}
    </div>
  );
}
