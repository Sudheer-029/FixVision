import { API_URL } from "@/lib/api";

export default function Home() {
  return (
    <main style={{ padding: "24px 16px", maxWidth: 640, margin: "0 auto" }}>
      <h1>FixVision</h1>
      <p>See it. Fix it. Verify it.</p>
      <p style={{ opacity: 0.6, fontSize: 14 }}>API: {API_URL}</p>
    </main>
  );
}
