"use client";

import { useState, useEffect, useCallback } from "react";

interface BriefingStats {
    tasksCompleted: number;
    emailsProcessed: number;
    socialPosts: number;
    approvalsPending: number;
    revenue: number;
    expenses: number;
    timeSaved: string;
}

interface Activity {
    type: "email" | "social" | "system";
    icon: string;
    title: string;
    time: string;
    status: "completed";
}

export default function BriefingPage() {
    const [stats, setStats] = useState<BriefingStats>({
        tasksCompleted: 0,
        emailsProcessed: 0,
        socialPosts: 0,
        approvalsPending: 0,
        revenue: 0,
        expenses: 0,
        timeSaved: "0h",
    });
    const [activities, setActivities] = useState<Activity[]>([]);
    const [briefing, setBriefing] = useState("");
    const [briefingDate, setBriefingDate] = useState("");
    const [loading, setLoading] = useState(true);

    const fetchBriefing = useCallback(async () => {
        try {
            const res = await fetch(`/api/briefing?t=${Date.now()}`, { cache: 'no-store' });
            const data = await res.json();
            setStats(data.stats || stats);
            setActivities(data.activities || []);
            setBriefing(data.briefing || "");
            setBriefingDate(data.briefingDate || "");
        } catch (error) {
            console.error("Failed to fetch briefing:", error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchBriefing();
        const interval = setInterval(fetchBriefing, 30000);
        return () => clearInterval(interval);
    }, [fetchBriefing]);

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(amount);
    };

    if (loading) {
        return (
            <div>
                <div className="skeleton" style={{ height: 32, width: 200, marginBottom: 24 }} />
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 24 }}>
                    {[1, 2, 3, 4].map(i => <div key={i} className="skeleton" style={{ height: 80, borderRadius: 12 }} />)}
                </div>
            </div>
        );
    }

    const netProfit = stats.revenue - stats.expenses;

    return (
        <div>
            {/* Header */}
            <div style={{ marginBottom: 24 }}>
                <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>CEO Briefing</h1>
                <p style={{ fontSize: 14, color: "var(--text-muted)" }}>
                    {briefingDate ? `Week of ${briefingDate}` : `Generated ${new Date().toLocaleDateString()}`}
                </p>
            </div>

            {/* Key Metrics */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 12, marginBottom: 24 }}>
                <div className="stat-card">
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8 }}>Revenue (MTD)</div>
                    <div className="stat-value" style={{ color: "var(--success)" }}>{formatCurrency(stats.revenue)}</div>
                </div>
                <div className="stat-card">
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8 }}>Expenses (MTD)</div>
                    <div className="stat-value" style={{ color: "var(--danger)" }}>{formatCurrency(stats.expenses)}</div>
                </div>
                <div className="stat-card">
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8 }}>Net Profit</div>
                    <div className="stat-value" style={{ color: netProfit >= 0 ? "var(--success)" : "var(--danger)" }}>{formatCurrency(netProfit)}</div>
                </div>
                <div className="stat-card">
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8 }}>Tasks Completed</div>
                    <div className="stat-value">{stats.tasksCompleted}</div>
                </div>
                <div className="stat-card">
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8 }}>Emails Processed</div>
                    <div className="stat-value">{stats.emailsProcessed}</div>
                </div>
                <div className="stat-card">
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8 }}>Social Posts</div>
                    <div className="stat-value">{stats.socialPosts}</div>
                </div>
                <div className="stat-card" style={{ background: stats.approvalsPending > 0 ? "var(--warning-light)" : undefined }}>
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8 }}>Pending Approvals</div>
                    <div className="stat-value" style={{ color: stats.approvalsPending > 0 ? "var(--warning)" : undefined }}>{stats.approvalsPending}</div>
                </div>
                <div className="stat-card">
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8 }}>Time Saved</div>
                    <div className="stat-value" style={{ fontSize: 20 }}>{stats.timeSaved}</div>
                </div>
            </div>

            {/* Briefing Content or Recent Activity */}
            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 20 }} className="briefing-grid">
                <div className="card">
                    <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>
                        {briefing ? "Latest Briefing" : "Business Summary"}
                    </h3>
                    {briefing ? (
                        <div style={{ fontSize: 13, lineHeight: 1.6, color: "var(--text-primary)" }}>
                            <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit", margin: 0 }}>{briefing.substring(0, 1500)}</pre>
                        </div>
                    ) : (
                        <div>
                            <div style={{ marginBottom: 20 }}>
                                <h4 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Executive Summary</h4>
                                <p style={{ fontSize: 13, lineHeight: 1.6, color: "var(--text-secondary)" }}>
                                    Your AI Employee has completed {stats.tasksCompleted} tasks,
                                    processing {stats.emailsProcessed} emails and managing {stats.socialPosts} social posts.
                                    Current month revenue stands at {formatCurrency(stats.revenue)} with net profit of {formatCurrency(netProfit)}.
                                </p>
                            </div>
                            {stats.approvalsPending > 0 && (
                                <div style={{ padding: 12, background: "var(--warning-light)", borderRadius: 8, borderLeft: "3px solid var(--warning)" }}>
                                    <p style={{ fontSize: 13, margin: 0, color: "var(--warning)" }}>
                                        ⚠️ {stats.approvalsPending} item{stats.approvalsPending > 1 ? 's' : ''} awaiting your approval
                                    </p>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                <div className="card">
                    <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Recent Activity</h3>
                    {activities.length === 0 ? (
                        <div style={{ textAlign: "center", padding: 30, color: "var(--text-muted)" }}>
                            <div style={{ fontSize: 32, marginBottom: 8 }}>📊</div>
                            <p style={{ fontSize: 12, margin: 0 }}>No recent activity</p>
                        </div>
                    ) : (
                        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                            {activities.map((activity, i) => (
                                <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: 10, background: "var(--bg-tertiary)", borderRadius: 6 }}>
                                    <span style={{ fontSize: 18 }}>{activity.icon}</span>
                                    <div style={{ flex: 1, minWidth: 0 }}>
                                        <div style={{ fontSize: 12, fontWeight: 500, color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                            {activity.title}
                                        </div>
                                        <div style={{ fontSize: 10, color: "var(--text-muted)" }}>
                                            {activity.time}
                                        </div>
                                    </div>
                                    <span className="badge badge-success" style={{ fontSize: 10 }}>✓</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            <style jsx>{`
                @media (max-width: 768px) {
                    .briefing-grid { grid-template-columns: 1fr; }
                }
            `}</style>
        </div>
    );
}
