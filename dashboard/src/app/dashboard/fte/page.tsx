"use client";

import { useState, useEffect, useCallback } from "react";

interface Service {
    name: string;
    displayName: string;
    status: "running" | "stopped" | "error";
    lastActive?: string;
    description: string;
}

interface FTEStatus {
    running: boolean;
    uptime: string;
    services: Service[];
    engine: string;
    mode: string;
}

interface LogEntry {
    time: string;
    level: string;
    message: string;
    source: string;
}

export default function FTEControlPage() {
    const [status, setStatus] = useState<FTEStatus>({
        running: false,
        uptime: "0h 0m",
        services: [],
        engine: "qwen",
        mode: "dry_run"
    });
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [engine, setEngine] = useState("qwen");

    const serviceDefinitions: Record<string, { displayName: string; description: string }> = {
        orchestrator: { displayName: "Orchestrator", description: "Main brain - processes tasks and generates plans" },
        gmail_watcher: { displayName: "Gmail Watcher", description: "Monitors inbox for new emails" },
        whatsapp_watcher: { displayName: "WhatsApp Watcher", description: "Monitors WhatsApp messages" },
        linkedin_watcher: { displayName: "LinkedIn Watcher", description: "Monitors LinkedIn activity" },
        odoo_watcher: { displayName: "Odoo Watcher", description: "Syncs accounting data from Odoo" },
    };

    const fetchStatus = useCallback(async () => {
        try {
            const ts = Date.now();
            const [statusRes, logsRes, engineRes] = await Promise.all([
                fetch(`/api/fte/status?t=${ts}`, { cache: 'no-store' }),
                fetch(`/api/logs?t=${ts}`, { cache: 'no-store' }),
                fetch(`/api/fte/engine?t=${ts}`, { cache: 'no-store' }),
            ]);

            const [statusData, logsData, engineData] = await Promise.all([
                statusRes.json(),
                logsRes.json(),
                engineRes.json(),
            ]);

            // Map services with definitions
            const mappedServices = (statusData.services || []).map((s: any) => ({
                ...s,
                displayName: serviceDefinitions[s.name]?.displayName || s.name,
                description: serviceDefinitions[s.name]?.description || "",
            }));

            setStatus({
                running: statusData.running,
                uptime: statusData.uptime || "0h 0m",
                services: mappedServices,
                engine: engineData.engine || "qwen",
                mode: engineData.mode || "dry_run"
            });

            setEngine(engineData.engine || "qwen");

            // Format logs
            const formattedLogs = (logsData.logs || []).slice(0, 20).map((log: any) => ({
                time: new Date(log.timestamp).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
                level: log.level,
                message: log.message,
                source: log.source,
            }));
            setLogs(formattedLogs);

        } catch (error) {
            console.error("Failed to fetch FTE status:", error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, [fetchStatus]);

    const handleStart = async () => {
        setActionLoading("start");
        try {
            const res = await fetch("/api/fte/start", { method: "POST" });
            const data = await res.json();
            if (data.success) {
                await fetchStatus();
            } else {
                alert("Failed to start: " + (data.error || "Unknown error"));
            }
        } catch (error) {
            alert("Failed to start FTE");
        } finally {
            setActionLoading(null);
        }
    };

    const handleStop = async () => {
        setActionLoading("stop");
        try {
            const res = await fetch("/api/fte/stop", { method: "POST" });
            const data = await res.json();
            if (data.success) {
                await fetchStatus();
            } else {
                alert("Failed to stop: " + (data.error || "Unknown error"));
            }
        } catch (error) {
            alert("Failed to stop FTE");
        } finally {
            setActionLoading(null);
        }
    };

    const handleEngineChange = async (newEngine: string) => {
        setActionLoading("engine");
        try {
            const res = await fetch("/api/fte/engine", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ engine: newEngine }),
            });
            const data = await res.json();
            if (data.success) {
                setEngine(newEngine);
                await fetchStatus();
            }
        } catch (error) {
            console.error("Failed to change engine:", error);
        } finally {
            setActionLoading(null);
        }
    };

    const getLevelColor = (level: string) => {
        switch (level?.toLowerCase()) {
            case "error": return "var(--danger)";
            case "warning": case "warn": return "var(--warning)";
            case "success": return "var(--success)";
            default: return "var(--text-muted)";
        }
    };

    if (loading) {
        return (
            <div>
                <div className="skeleton" style={{ height: 32, width: 200, marginBottom: 24 }} />
                <div className="skeleton" style={{ height: 200, borderRadius: 12, marginBottom: 16 }} />
                <div className="skeleton" style={{ height: 300, borderRadius: 12 }} />
            </div>
        );
    }

    const runningCount = status.services.filter(s => s.status === "running").length;

    return (
        <div>
            {/* Header */}
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 16, marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>FTE Control Center</h1>
                    <p style={{ fontSize: 14, color: "var(--text-muted)" }}>Manage your AI Employee services and configuration</p>
                </div>
            </div>

            {/* Main Status Card */}
            <div className="card" style={{ marginBottom: 24, padding: 24 }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 20 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                        <div style={{
                            width: 64, height: 64, borderRadius: 16,
                            background: status.running ? "var(--success-light)" : "var(--bg-tertiary)",
                            display: "flex", alignItems: "center", justifyContent: "center",
                            fontSize: 32
                        }}>
                            🤖
                        </div>
                        <div>
                            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                                <div style={{
                                    width: 10, height: 10, borderRadius: 5,
                                    background: status.running ? "var(--success)" : "var(--text-muted)",
                                    animation: status.running ? "pulse 2s infinite" : "none"
                                }} />
                                <span style={{ fontSize: 18, fontWeight: 600, color: status.running ? "var(--success)" : "var(--text-muted)" }}>
                                    {status.running ? "Online" : "Offline"}
                                </span>
                            </div>
                            <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
                                {runningCount} of {status.services.length} services running
                            </div>
                        </div>
                    </div>
                    <div style={{ display: "flex", gap: 12 }}>
                        {status.running ? (
                            <>
                                <button
                                    onClick={handleStop}
                                    disabled={actionLoading !== null}
                                    className="btn btn-danger"
                                    style={{ minWidth: 100 }}
                                >
                                    {actionLoading === "stop" ? "Stopping..." : "Stop FTE"}
                                </button>
                                <button
                                    onClick={async () => { await handleStop(); setTimeout(handleStart, 1000); }}
                                    disabled={actionLoading !== null}
                                    className="btn btn-secondary"
                                >
                                    Restart
                                </button>
                            </>
                        ) : (
                            <button
                                onClick={handleStart}
                                disabled={actionLoading !== null}
                                className="btn btn-success"
                                style={{ minWidth: 120 }}
                            >
                                {actionLoading === "start" ? "Starting..." : "Start FTE"}
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Configuration */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 24 }} className="config-grid">
                {/* Reasoning Engine */}
                <div className="card">
                    <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Reasoning Engine</h3>
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                        {[
                            { id: "qwen", name: "Qwen (Local)", desc: "Fast, runs locally, good for most tasks" },
                            { id: "claude", name: "Claude (Cloud)", desc: "More capable, requires API key" },
                        ].map((eng) => (
                            <label
                                key={eng.id}
                                style={{
                                    display: "flex", alignItems: "center", gap: 12, padding: 12, borderRadius: 8,
                                    background: engine === eng.id ? "var(--primary-light)" : "var(--bg-tertiary)",
                                    border: `1px solid ${engine === eng.id ? "var(--primary)" : "transparent"}`,
                                    cursor: "pointer", transition: "all 0.15s"
                                }}
                            >
                                <input
                                    type="radio"
                                    name="engine"
                                    checked={engine === eng.id}
                                    onChange={() => handleEngineChange(eng.id)}
                                    disabled={actionLoading === "engine"}
                                />
                                <div>
                                    <div style={{ fontSize: 13, fontWeight: 500 }}>{eng.name}</div>
                                    <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{eng.desc}</div>
                                </div>
                            </label>
                        ))}
                    </div>
                </div>

                {/* Quick Stats */}
                <div className="card">
                    <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>System Info</h3>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                        <div>
                            <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>Engine</div>
                            <div style={{ fontSize: 14, fontWeight: 500, textTransform: "capitalize" }}>{engine}</div>
                        </div>
                        <div>
                            <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>Mode</div>
                            <div style={{ fontSize: 14, fontWeight: 500 }}>
                                <span className={`badge ${status.mode === "live" ? "badge-success" : "badge-warning"}`}>
                                    {status.mode === "live" ? "Live" : "Dry Run"}
                                </span>
                            </div>
                        </div>
                        <div>
                            <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>Services</div>
                            <div style={{ fontSize: 14, fontWeight: 500 }}>{runningCount}/{status.services.length}</div>
                        </div>
                        <div>
                            <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>Status</div>
                            <div style={{ fontSize: 14, fontWeight: 500, color: status.running ? "var(--success)" : "var(--text-muted)" }}>
                                {status.running ? "Active" : "Inactive"}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Services */}
            <div className="card" style={{ marginBottom: 24 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Services</h3>
                <div style={{ display: "grid", gap: 12 }}>
                    {status.services.map((service) => (
                        <div
                            key={service.name}
                            style={{
                                display: "flex", alignItems: "center", gap: 12, padding: 16,
                                background: "var(--bg-tertiary)", borderRadius: 8
                            }}
                        >
                            <div style={{
                                width: 10, height: 10, borderRadius: 5,
                                background: service.status === "running" ? "var(--success)" : service.status === "error" ? "var(--danger)" : "var(--text-muted)"
                            }} />
                            <div style={{ flex: 1 }}>
                                <div style={{ fontSize: 14, fontWeight: 500 }}>{service.displayName}</div>
                                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{service.description}</div>
                            </div>
                            <span className={`badge ${service.status === "running" ? "badge-success" : service.status === "error" ? "badge-danger" : "badge-secondary"}`}>
                                {service.status}
                            </span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Live Logs */}
            <div className="card">
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                    <h3 style={{ fontSize: 14, fontWeight: 600, margin: 0 }}>Live Logs</h3>
                    <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Auto-refreshing every 5s</span>
                </div>
                <div style={{
                    background: "#1a1a2e", borderRadius: 8, padding: 16, maxHeight: 300, overflowY: "auto",
                    fontFamily: "monospace", fontSize: 12
                }}>
                    {logs.length === 0 ? (
                        <div style={{ color: "#666", textAlign: "center", padding: 20 }}>No recent logs</div>
                    ) : (
                        logs.map((log, i) => (
                            <div key={i} style={{ display: "flex", gap: 12, marginBottom: 4, color: "#e0e0e0" }}>
                                <span style={{ color: "#666", minWidth: 70 }}>{log.time}</span>
                                <span style={{ color: getLevelColor(log.level), minWidth: 50, textTransform: "uppercase", fontSize: 10 }}>{log.level}</span>
                                <span style={{ color: "#888", minWidth: 100 }}>[{log.source}]</span>
                                <span style={{ flex: 1, wordBreak: "break-word" }}>{log.message}</span>
                            </div>
                        ))
                    )}
                </div>
            </div>

            <style jsx>{`
                @media (max-width: 768px) {
                    .config-grid { grid-template-columns: 1fr; }
                }
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
            `}</style>
        </div>
    );
}
