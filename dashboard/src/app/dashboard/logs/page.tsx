"use client";

import { useState, useEffect, useCallback } from "react";

interface LogEntry {
    id: string;
    timestamp: string;
    level: "info" | "warn" | "error" | "success";
    source: string;
    message: string;
}

export default function LogsPage() {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState("all");
    const [autoRefresh, setAutoRefresh] = useState(true);

    const fetchLogs = useCallback(async () => {
        try {
            const res = await fetch(`/api/logs?t=${Date.now()}`, {
                cache: 'no-store'
            });
            const data = await res.json();
            setLogs(data.logs || []);
        } catch (error) {
            console.error("Failed to fetch logs:", error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchLogs();
        if (autoRefresh) {
            const interval = setInterval(fetchLogs, 5000);
            return () => clearInterval(interval);
        }
    }, [fetchLogs, autoRefresh]);

    const filtered = filter === "all" ? logs : logs.filter(l => l.level === filter);

    const getLevelColor = (level: string) => {
        switch (level) {
            case "error": return "var(--danger)";
            case "warn": return "var(--warning)";
            case "success": return "var(--success)";
            default: return "var(--text-muted)";
        }
    };

    const getLevelBg = (level: string) => {
        switch (level) {
            case "error": return "var(--danger-light)";
            case "warn": return "var(--warning-light)";
            case "success": return "var(--success-light)";
            default: return "var(--bg-tertiary)";
        }
    };

    if (loading) {
        return (
            <div>
                <div className="skeleton" style={{ height: 32, width: 200, marginBottom: 24 }} />
                <div className="skeleton" style={{ height: 400, borderRadius: 12 }} />
            </div>
        );
    }

    const stats = {
        total: logs.length,
        errors: logs.filter(l => l.level === "error").length,
        warnings: logs.filter(l => l.level === "warn").length,
    };

    return (
        <div>
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 16, marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>System Logs</h1>
                    <p style={{ fontSize: 14, color: "var(--text-muted)" }}>Real-time activity and debug information</p>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <span className={`status-dot ${autoRefresh ? "status-online" : "status-offline"}`} style={{ animation: autoRefresh ? "pulse 2s infinite" : "none" }} />
                        <span style={{ fontSize: 13, color: "var(--text-muted)" }}>{autoRefresh ? "Live" : "Paused"}</span>
                    </div>
                    <button onClick={() => setAutoRefresh(!autoRefresh)} className="btn btn-secondary btn-sm">
                        {autoRefresh ? "Pause" : "Resume"}
                    </button>
                    <button onClick={fetchLogs} className="btn btn-secondary btn-sm">↻ Refresh</button>
                </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 12, marginBottom: 24 }}>
                <div className="stat-card">
                    <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>Total Entries</div>
                    <div className="stat-value">{stats.total}</div>
                </div>
                <div className="stat-card" style={{ background: stats.errors > 0 ? "var(--danger-light)" : undefined }}>
                    <div style={{ fontSize: 12, color: stats.errors > 0 ? "var(--danger)" : "var(--text-muted)", marginBottom: 4 }}>Errors</div>
                    <div className="stat-value" style={{ color: stats.errors > 0 ? "var(--danger)" : undefined }}>{stats.errors}</div>
                </div>
                <div className="stat-card" style={{ background: stats.warnings > 0 ? "var(--warning-light)" : undefined }}>
                    <div style={{ fontSize: 12, color: stats.warnings > 0 ? "var(--warning)" : "var(--text-muted)", marginBottom: 4 }}>Warnings</div>
                    <div className="stat-value" style={{ color: stats.warnings > 0 ? "var(--warning)" : undefined }}>{stats.warnings}</div>
                </div>
            </div>

            <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
                {["all", "info", "success", "warn", "error"].map(f => (
                    <button
                        key={f}
                        onClick={() => setFilter(f)}
                        className={`btn btn-sm ${filter === f ? "btn-primary" : "btn-secondary"}`}
                        style={{ textTransform: "capitalize" }}
                    >
                        {f}
                        {f !== "all" && ` (${logs.filter(l => l.level === f).length})`}
                    </button>
                ))}
            </div>

            {filtered.length === 0 ? (
                <div className="card" style={{ textAlign: "center", padding: 40 }}>
                    <div style={{ fontSize: 48, marginBottom: 16 }}>📋</div>
                    <h3 style={{ fontSize: 18, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>No logs found</h3>
                    <p style={{ fontSize: 14, color: "var(--text-muted)" }}>Start the FTE to generate logs</p>
                </div>
            ) : (
                <div className="card" style={{ padding: 0, overflow: "hidden" }}>
                    <div style={{ maxHeight: 600, overflowY: "auto" }}>
                        {filtered.map((log, i) => (
                            <div
                                key={log.id}
                                style={{
                                    display: "grid",
                                    gridTemplateColumns: "100px 60px 100px 1fr",
                                    gap: 16,
                                    padding: "12px 16px",
                                    background: i % 2 === 0 ? "transparent" : "var(--bg-tertiary)",
                                    fontFamily: "monospace",
                                    fontSize: 12,
                                    alignItems: "flex-start"
                                }}
                            >
                                <span style={{ color: "var(--text-muted)" }}>
                                    {new Date(log.timestamp).toLocaleTimeString()}
                                </span>
                                <span style={{
                                    fontWeight: 600,
                                    textTransform: "uppercase",
                                    color: getLevelColor(log.level),
                                    padding: "2px 6px",
                                    borderRadius: 4,
                                    background: getLevelBg(log.level),
                                    textAlign: "center"
                                }}>
                                    {log.level}
                                </span>
                                <span style={{ color: "var(--text-secondary)" }}>[{log.source}]</span>
                                <span style={{ color: "var(--text-primary)", wordBreak: "break-word" }}>{log.message}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
