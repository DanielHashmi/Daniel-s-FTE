"use client";

import { useState, useEffect } from "react";

interface Settings {
    dryRun: boolean;
    hitl: boolean;
    gmailInterval: number;
    socialInterval: number;
}

interface Integration {
    id: string;
    name: string;
    icon: string;
    connected: boolean;
    account?: string;
    envKey: string;
}

export default function SettingsPage() {
    const [settings, setSettings] = useState<Settings>({
        dryRun: true,
        hitl: true,
        gmailInterval: 60,
        socialInterval: 300,
    });
    const [integrations, setIntegrations] = useState<Integration[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const res = await fetch("/api/settings");
                const data = await res.json();
                setSettings(data.settings || settings);
                setIntegrations(data.integrations || []);
            } catch (error) {
                console.error("Failed to fetch settings:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchSettings();
    }, []);

    const handleToggle = async (key: keyof Settings) => {
        const newValue = !settings[key];
        setSettings(prev => ({ ...prev, [key]: newValue }));

        try {
            await fetch("/api/settings", {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ [key]: newValue }),
            });
        } catch (error) {
            console.error("Failed to save setting:", error);
            setSettings(prev => ({ ...prev, [key]: !newValue }));
        }
    };

    if (loading) {
        return (
            <div>
                <div className="skeleton" style={{ height: 32, width: 200, marginBottom: 24 }} />
                <div className="skeleton" style={{ height: 200, borderRadius: 12, marginBottom: 24 }} />
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 12 }}>
                    {[1, 2, 3, 4].map(i => <div key={i} className="skeleton" style={{ height: 80, borderRadius: 12 }} />)}
                </div>
            </div>
        );
    }

    const defaultIntegrations: Integration[] = [
        { id: "twitter", name: "Twitter/X", icon: "🐦", connected: true, account: "@connected", envKey: "TWITTER_API_KEY" },
        { id: "linkedin", name: "LinkedIn", icon: "💼", connected: false, envKey: "LINKEDIN_ACCESS_TOKEN" },
        { id: "facebook", name: "Facebook", icon: "📘", connected: false, envKey: "FACEBOOK_PAGE_TOKEN" },
        { id: "instagram", name: "Instagram", icon: "📷", connected: false, envKey: "INSTAGRAM_ACCESS_TOKEN" },
        { id: "gmail", name: "Gmail", icon: "📧", connected: false, envKey: "GMAIL_CREDENTIALS_PATH" },
        { id: "odoo", name: "Odoo", icon: "🔷", connected: false, envKey: "ODOO_URL" },
    ];

    const displayIntegrations = integrations.length > 0 ? integrations : defaultIntegrations;

    return (
        <div>
            <div style={{ marginBottom: 24 }}>
                <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>Settings</h1>
                <p style={{ fontSize: 14, color: "var(--text-muted)" }}>Configure FTE preferences and integrations</p>
            </div>

            <div style={{ marginBottom: 32 }}>
                <h2 className="section-title" style={{ marginBottom: 12 }}>General Settings</h2>
                <div className="card">
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 0" }}>
                        <div>
                            <div style={{ fontSize: 14, fontWeight: 500, color: "var(--text-primary)" }}>Dry Run Mode</div>
                            <div style={{ fontSize: 13, color: "var(--text-muted)" }}>Simulate actions without actually executing them</div>
                        </div>
                        <button
                            onClick={() => handleToggle("dryRun")}
                            className={`toggle ${settings.dryRun ? "active" : ""}`}
                            aria-label="Toggle dry run mode"
                        />
                    </div>

                    <div style={{ height: 1, background: "var(--border-color)" }} />

                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 0" }}>
                        <div>
                            <div style={{ fontSize: 14, fontWeight: 500, color: "var(--text-primary)" }}>Human-in-the-Loop (HITL)</div>
                            <div style={{ fontSize: 13, color: "var(--text-muted)" }}>Require manual approval before executing actions</div>
                        </div>
                        <button
                            onClick={() => handleToggle("hitl")}
                            className={`toggle ${settings.hitl ? "active" : ""}`}
                            aria-label="Toggle HITL mode"
                        />
                    </div>
                </div>
            </div>

            <div style={{ marginBottom: 32 }}>
                <h2 className="section-title" style={{ marginBottom: 12 }}>Check Intervals</h2>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 }}>
                    <div className="card">
                        <div style={{ fontSize: 14, fontWeight: 500, color: "var(--text-primary)", marginBottom: 8 }}>Gmail Check</div>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <span className="stat-value">{settings.gmailInterval}s</span>
                            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>interval</span>
                        </div>
                    </div>
                    <div className="card">
                        <div style={{ fontSize: 14, fontWeight: 500, color: "var(--text-primary)", marginBottom: 8 }}>Social Media</div>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <span className="stat-value">{settings.socialInterval}s</span>
                            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>interval</span>
                        </div>
                    </div>
                </div>
            </div>

            <div style={{ marginBottom: 32 }}>
                <h2 className="section-title" style={{ marginBottom: 12 }}>Integrations</h2>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12 }}>
                    {displayIntegrations.map(i => (
                        <div key={i.id} className="card" style={{ display: "flex", alignItems: "center", gap: 12 }}>
                            <span style={{ fontSize: 32 }}>{i.icon}</span>
                            <div style={{ flex: 1 }}>
                                <div style={{ fontSize: 14, fontWeight: 500, color: "var(--text-primary)" }}>{i.name}</div>
                                {i.connected ? (
                                    <div style={{ fontSize: 12, color: "var(--success)" }}>{i.account || "Connected"}</div>
                                ) : (
                                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Set {i.envKey} in .env</div>
                                )}
                            </div>
                            <span className={`status-dot ${i.connected ? "status-online" : "status-offline"}`} />
                        </div>
                    ))}
                </div>
                <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 12 }}>
                    💡 Configure integrations by adding API keys to the <code style={{ background: "var(--bg-tertiary)", padding: "2px 6px", borderRadius: 4 }}>.env</code> file in the project root
                </p>
            </div>

            <div>
                <h2 className="section-title" style={{ marginBottom: 12, color: "var(--danger)" }}>Danger Zone</h2>
                <div className="card">
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                        <div>
                            <div style={{ fontSize: 14, fontWeight: 500, color: "var(--text-primary)" }}>Reset All Settings</div>
                            <div style={{ fontSize: 13, color: "var(--text-muted)" }}>This will reset all preferences to defaults</div>
                        </div>
                        <button className="btn btn-danger">Reset</button>
                    </div>
                </div>
            </div>
        </div>
    );
}
