"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
    const stored = localStorage.getItem("theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.setAttribute("data-theme", stored || (prefersDark ? "dark" : "light"));
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });

      if (res.ok) {
        router.push("/dashboard");
      } else {
        setError("Invalid password");
      }
    } catch {
      setError("Connection error");
    } finally {
      setLoading(false);
    }
  };

  if (!mounted) return null;

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: 24, background: "var(--bg-primary)" }}>
      <div style={{ width: "100%", maxWidth: 360 }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{ width: 64, height: 64, margin: "0 auto 16px", borderRadius: 16, background: "var(--bg-secondary)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 32 }}>
            🤖
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>Daniel FTE</h1>
          <p style={{ fontSize: 14, color: "var(--text-muted)" }}>Your Personal AI Employee</p>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 6, marginTop: 12, padding: "4px 10px", borderRadius: 20, background: "var(--success-light)", fontSize: 12, fontWeight: 500, color: "var(--success)" }}>
            <span className="status-dot status-online" />
            Online
          </div>
        </div>

        {/* Form */}
        <div className="card" style={{ padding: 24 }}>
          <form onSubmit={handleLogin}>
            <div style={{ marginBottom: 20 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 500, color: "var(--text-secondary)", marginBottom: 8 }}>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                placeholder="Enter password"
                autoFocus
                required
              />
            </div>

            {error && (
              <div style={{ display: "flex", alignItems: "center", gap: 8, padding: 12, marginBottom: 16, borderRadius: 8, background: "var(--danger-light)", fontSize: 13, fontWeight: 500, color: "var(--danger)" }}>
                ⚠️ {error}
              </div>
            )}

            <button type="submit" disabled={loading} className="btn btn-primary btn-lg" style={{ width: "100%" }}>
              {loading ? <span className="spinner" /> : "Access Dashboard"}
            </button>
          </form>
        </div>

        {/* Footer */}
        <p style={{ textAlign: "center", fontSize: 12, color: "var(--text-muted)", marginTop: 24 }}>
          AI Employee Hackathon 2026
        </p>
      </div>
    </div>
  );
}
