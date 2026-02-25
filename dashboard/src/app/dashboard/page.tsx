"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";

interface FTEStatus {
    running: boolean;
    uptime: string;
    services: Array<{ name: string; status: string; lastActive?: string }>;
}

interface Approval {
    id: string;
    title: string;
    type: string;
    priority: string;
    timestamp: string;
    platform?: string;
}

interface Email {
    id: string;
    from: string;
    subject: string;
    time: string;
    priority: string;
}

interface Stats {
    revenue: number;
    pendingApprovals: number;
    emailsToday: number;
    tasksCompleted: number;
    plansActive: number;
}

export default function DashboardPage() {
    const [fteStatus, setFteStatus] = useState<FTEStatus>({ running: false, uptime: "0h 0m", services: [] });
    const [approvals, setApprovals] = useState<Approval[]>([]);
    const [emails, setEmails] = useState<Email[]>([]);
    const [stats, setStats] = useState<Stats>({ revenue: 0, pendingApprovals: 0, emailsToday: 0, tasksCompleted: 0, plansActive: 0 });
    const [loading, setLoading] = useState(true);

    const fetchData = useCallback(async () => {
        try {
            const ts = Date.now();
            const opts = { cache: 'no-store' as RequestCache };

            const [fteRes, approvalsRes, emailsRes, odooRes, statsRes] = await Promise.all([
                fetch(`/api/fte/status?t=${ts}`, opts),
                fetch(`/api/approvals?t=${ts}`, opts),
                fetch(`/api/email/inbox?t=${ts}`, opts),
                fetch(`/api/odoo/summary?t=${ts}&autoSync=false`, opts),
                fetch(`/api/dashboard/stats?t=${ts}`, opts),
            ]);

            const [fteData, approvalsData, emailsData, odooData, statsData] = await Promise.all([
                fteRes.json(),
                approvalsRes.json(),
                emailsRes.json(),
                odooRes.json(),
                statsRes.json(),
            ]);

            setFteStatus(fteData);
            setApprovals((approvalsData.approvals || []).slice(0, 5));
            setEmails((emailsData.emails || []).slice(0, 5));
            setStats({
                revenue: odooData.stats?.revenue || 0,
                pendingApprovals: approvalsData.approvals?.length || 0,
                emailsToday: emailsData.emails?.length || 0,
                tasksCompleted: statsData.tasksToday || 0,
                plansActive: statsData.plansActive || 0,
            });
        } catch (error) {
            console.error("Failed to fetch dashboard data:", error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, [fetchData]);

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(amount);
    };

    const formatTime = (timestamp: string) => {
        if (!timestamp) return "";
        const date = new Date(timestamp);
        return date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
    };

    if (loading) {
        return (
            <div>
                <div className="skeleton" style={{ height: 32, width: 300, marginBottom: 24 }} />
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 24 }}>
                    {[1, 2, 3, 4].map(i => <div key={i} className="skeleton" style={{ height: 100, borderRadius: 12 }} />)}
                </div>
            </div>
        );
    }

    const runningServices = fteStatus.services.filter(s => s.status === "running").length;

    return (
        <div>
            {/* Header with Live Status */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: 28, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>
                        Command Center
                    </h1>
                    <p style={{ fontSize: 14, color: "var(--text-muted)" }}>
                        {new Date().toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
                    </p>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <div style={{
                        display: "flex", alignItems: "center", gap: 8,
                        padding: "8px 16px", borderRadius: 20,
                        background: fteStatus.running ? "var(--success-light)" : "var(--bg-tertiary)",
                        border: `1px solid ${fteStatus.running ? "var(--success)" : "var(--border-color)"}`
                    }}>
                        <div style={{
                            width: 8, height: 8, borderRadius: 4,
                            background: fteStatus.running ? "var(--success)" : "var(--text-muted)",
                            animation: fteStatus.running ? "pulse 2s infinite" : "none"
                        }} />
                        <span style={{ fontSize: 13, fontWeight: 500, color: fteStatus.running ? "var(--success)" : "var(--text-muted)" }}>
                            {fteStatus.running ? "AI Employee Online" : "AI Employee Offline"}
                        </span>
                    </div>
                </div>
            </div>

            {/* Key Metrics */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginBottom: 24 }}>
                <div className="stat-card" style={{ background: "linear-gradient(135deg, var(--success-light) 0%, var(--bg-secondary) 100%)" }}>
                    <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 8 }}>Revenue (MTD)</div>
                    <div className="stat-value" style={{ color: "var(--success)", fontSize: 24 }}>{formatCurrency(stats.revenue)}</div>
                    <Link href="/dashboard/accounting" style={{ fontSize: 11, color: "var(--primary)", textDecoration: "none" }}>View Details →</Link>
                </div>
                <div className="stat-card" style={{ background: stats.pendingApprovals > 0 ? "linear-gradient(135deg, var(--warning-light) 0%, var(--bg-secondary) 100%)" : undefined }}>
                    <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 8 }}>Pending Approvals</div>
                    <div className="stat-value" style={{ color: stats.pendingApprovals > 0 ? "var(--warning)" : undefined, fontSize: 24 }}>{stats.pendingApprovals}</div>
                    <Link href="/dashboard/approvals" style={{ fontSize: 11, color: "var(--primary)", textDecoration: "none" }}>Review Now →</Link>
                </div>
                <div className="stat-card">
                    <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 8 }}>Emails Today</div>
                    <div className="stat-value" style={{ fontSize: 24 }}>{stats.emailsToday}</div>
                    <Link href="/dashboard/email" style={{ fontSize: 11, color: "var(--primary)", textDecoration: "none" }}>View Inbox →</Link>
                </div>
                <div className="stat-card">
                    <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 8 }}>Services Active</div>
                    <div className="stat-value" style={{ fontSize: 24 }}>{runningServices}/{fteStatus.services.length || 4}</div>
                    <Link href="/dashboard/fte" style={{ fontSize: 11, color: "var(--primary)", textDecoration: "none" }}>Manage FTE →</Link>
                </div>
            </div>

            {/* Main Content Grid */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }} className="dashboard-main-grid">
                {/* Pending Approvals */}
                <div className="card" style={{ padding: 0, overflow: "hidden" }}>
                    <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border-color)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <h2 style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>Pending Approvals</h2>
                        <Link href="/dashboard/approvals" className="btn btn-ghost btn-sm">View All</Link>
                    </div>
                    {approvals.length === 0 ? (
                        <div style={{ padding: 40, textAlign: "center" }}>
                            <div style={{ fontSize: 32, marginBottom: 8 }}>✅</div>
                            <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0 }}>All caught up! No pending approvals.</p>
                        </div>
                    ) : (
                        <div>
                            {approvals.map((item, i) => (
                                <Link
                                    key={item.id}
                                    href="/dashboard/approvals"
                                    style={{
                                        display: "flex", alignItems: "center", gap: 12, padding: "12px 20px",
                                        textDecoration: "none", borderTop: i > 0 ? "1px solid var(--border-color)" : "none",
                                        transition: "background 0.15s"
                                    }}
                                    className="hover-bg"
                                >
                                    <div style={{
                                        width: 36, height: 36, borderRadius: 8,
                                        background: item.type === "social" ? "#E3F2FD" : item.type === "email" ? "#FFF3E0" : "#F3E5F5",
                                        display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16
                                    }}>
                                        {item.type === "social" ? "📱" : item.type === "email" ? "✉️" : "📄"}
                                    </div>
                                    <div style={{ flex: 1, minWidth: 0 }}>
                                        <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text-primary)", marginBottom: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                            {item.title}
                                        </div>
                                        <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                                            {item.platform || item.type} • {formatTime(item.timestamp)}
                                        </div>
                                    </div>
                                    {item.priority === "high" && <span className="badge badge-danger">Urgent</span>}
                                </Link>
                            ))}
                        </div>
                    )}
                </div>

                {/* Recent Emails */}
                <div className="card" style={{ padding: 0, overflow: "hidden" }}>
                    <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border-color)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <h2 style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>Recent Emails</h2>
                        <Link href="/dashboard/email" className="btn btn-ghost btn-sm">View All</Link>
                    </div>
                    {emails.length === 0 ? (
                        <div style={{ padding: 40, textAlign: "center" }}>
                            <div style={{ fontSize: 32, marginBottom: 8 }}>📭</div>
                            <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0 }}>No new emails</p>
                        </div>
                    ) : (
                        <div>
                            {emails.map((email, i) => (
                                <div
                                    key={email.id}
                                    style={{
                                        display: "flex", alignItems: "center", gap: 12, padding: "12px 20px",
                                        borderTop: i > 0 ? "1px solid var(--border-color)" : "none"
                                    }}
                                >
                                    <div style={{
                                        width: 36, height: 36, borderRadius: 18,
                                        background: email.priority === "urgent" ? "var(--danger-light)" : "var(--bg-tertiary)",
                                        display: "flex", alignItems: "center", justifyContent: "center",
                                        fontSize: 13, fontWeight: 600, color: email.priority === "urgent" ? "var(--danger)" : "var(--text-muted)"
                                    }}>
                                        {email.from[0]?.toUpperCase() || "?"}
                                    </div>
                                    <div style={{ flex: 1, minWidth: 0 }}>
                                        <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text-primary)", marginBottom: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                            {email.subject}
                                        </div>
                                        <div style={{ fontSize: 11, color: "var(--text-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                            {email.from}
                                        </div>
                                    </div>
                                    <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{formatTime(email.time)}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Quick Actions */}
            <div style={{ marginTop: 24 }}>
                <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Quick Actions</h2>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12 }}>
                    {[
                        { href: "/dashboard/fte", icon: "🤖", label: "FTE Control", desc: fteStatus.running ? "Running" : "Stopped" },
                        { href: "/dashboard/accounting", icon: "💰", label: "Accounting", desc: "Odoo Sync" },
                        { href: "/dashboard/social", icon: "📱", label: "Social Media", desc: "Create Post" },
                        { href: "/dashboard/briefing", icon: "📊", label: "CEO Briefing", desc: "Weekly Report" },
                        { href: "/dashboard/logs", icon: "📋", label: "System Logs", desc: "Live Feed" },
                        { href: "/dashboard/settings", icon: "⚙️", label: "Settings", desc: "Configure" },
                    ].map((action, i) => (
                        <Link
                            key={i}
                            href={action.href}
                            className="card hover-bg"
                            style={{ textDecoration: "none", padding: 16, display: "flex", alignItems: "center", gap: 12 }}
                        >
                            <span style={{ fontSize: 24 }}>{action.icon}</span>
                            <div>
                                <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text-primary)" }}>{action.label}</div>
                                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{action.desc}</div>
                            </div>
                        </Link>
                    ))}
                </div>
            </div>

            <style jsx>{`
                @media (max-width: 768px) {
                    .dashboard-main-grid { grid-template-columns: 1fr; }
                }
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
                .hover-bg:hover { background: var(--bg-tertiary); }
            `}</style>
        </div>
    );
}
