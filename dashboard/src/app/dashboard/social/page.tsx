"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

interface SocialPost {
    id: string;
    platform: string;
    content: string;
    status: "pending" | "approved" | "posted";
    createdAt: string;
    brain?: string;
}

interface PlatformStatus {
    id: string;
    name: string;
    icon: string;
    connected: boolean;
    details?: string;
}

interface AccountsResponse {
    accounts?: Array<{
        id: string;
        name: string;
        icon?: string;
        connected: boolean;
        details?: string;
    }>;
    reasoningEngine?: string;
    dryRun?: boolean;
    orchestrator?: {
        running: boolean;
        lastHeartbeat: string | null;
        ageSeconds: number | null;
    };
    facebook?: {
        composerUrl: string | null;
        sessionDir: string;
        browserChannel: string | null;
        headless: boolean;
        keepOpenSeconds: number;
        loginWaitSeconds: number;
    };
}

function platformIcon(platform: string): string {
    if (platform === "facebook") return "FB";
    if (platform === "twitter") return "X";
    if (platform === "linkedin") return "IN";
    if (platform === "instagram") return "IG";
    return "SM";
}

const defaultPlatforms: PlatformStatus[] = [
    { id: "twitter", name: "Twitter/X", icon: "X", connected: false },
    { id: "linkedin", name: "LinkedIn", icon: "IN", connected: false },
    { id: "facebook", name: "Facebook (Qwen + Playwright)", icon: "FB", connected: false },
    { id: "instagram", name: "Instagram", icon: "IG", connected: false },
];

export default function SocialPage() {
    const [showModal, setShowModal] = useState(false);
    const [content, setContent] = useState("");
    const [qwenPrompt, setQwenPrompt] = useState("");
    const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
    const [posts, setPosts] = useState<SocialPost[]>([]);
    const [platforms, setPlatforms] = useState<PlatformStatus[]>(defaultPlatforms);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [error, setError] = useState("");
    const [notice, setNotice] = useState("");
    const [runtime, setRuntime] = useState<{
        reasoningEngine: string;
        dryRun: boolean;
        orchestrator?: AccountsResponse["orchestrator"];
        facebook?: AccountsResponse["facebook"];
    } | null>(null);

    const facebookSelected = selectedPlatforms.includes("facebook");
    const characterLimit = facebookSelected ? 2200 : 280;

    const canSubmit = useMemo(() => {
        const hasAnyText = Boolean(content.trim() || qwenPrompt.trim());
        const facebookReady = !facebookSelected || Boolean(qwenPrompt.trim());
        return selectedPlatforms.length > 0 && hasAnyText && facebookReady;
    }, [selectedPlatforms, content, qwenPrompt, facebookSelected]);

    const fetchPosts = useCallback(async () => {
        try {
            const res = await fetch(`/api/social/posts?t=${Date.now()}`, { cache: "no-store" });
            const data = await res.json();
            setPosts(data.posts || []);
        } catch (fetchError) {
            console.error("Failed to fetch posts:", fetchError);
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchAccounts = useCallback(async () => {
        try {
            const res = await fetch("/api/social/accounts", { cache: "no-store" });
            const data = (await res.json()) as AccountsResponse;
            if (Array.isArray(data.accounts) && data.accounts.length > 0) {
                setPlatforms(
                    data.accounts.map((account) => ({
                        id: String(account.id),
                        name: String(account.name),
                        icon: String(account.icon || platformIcon(String(account.id))),
                        connected: Boolean(account.connected),
                        details: account.details ? String(account.details) : undefined,
                    }))
                );
            }
            setRuntime({
                reasoningEngine: String(data.reasoningEngine || "qwen"),
                dryRun: Boolean(data.dryRun),
                orchestrator: data.orchestrator,
                facebook: data.facebook,
            });
        } catch (fetchError) {
            console.error("Failed to fetch social accounts:", fetchError);
        }
    }, []);

    useEffect(() => {
        void fetchPosts();
        void fetchAccounts();
        const postInterval = setInterval(fetchPosts, 10000);
        const accountInterval = setInterval(fetchAccounts, 30000);
        return () => {
            clearInterval(postInterval);
            clearInterval(accountInterval);
        };
    }, [fetchPosts, fetchAccounts]);

    const togglePlatform = (id: string) => {
        setSelectedPlatforms((prev) =>
            prev.includes(id) ? prev.filter((platform) => platform !== id) : [...prev, id]
        );
    };

    const handleGenerateFacebookDraft = async () => {
        if (!qwenPrompt.trim()) {
            setError("Enter a Qwen prompt first.");
            return;
        }

        setGenerating(true);
        setError("");
        try {
            const res = await fetch("/api/social/facebook/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt: qwenPrompt, seedContent: content }),
            });
            const data = await res.json();
            if (!res.ok || !data.success) {
                throw new Error(data.error || "Qwen generation failed");
            }
            setContent(data.generatedContent || "");
        } catch (generationError) {
            setError(
                generationError instanceof Error ? generationError.message : "Qwen generation failed"
            );
        } finally {
            setGenerating(false);
        }
    };

    const handleCreatePost = async (autoApprove = false) => {
        if (!canSubmit) return;

        setSubmitting(true);
        setError("");
        setNotice("");
        try {
            if (autoApprove) {
                const unsupported = selectedPlatforms.filter(
                    (p) => !["facebook", "twitter"].includes(String(p).toLowerCase())
                );
                if (unsupported.length > 0) {
                    setError(
                        `Approve & Post Now currently supports only Facebook and Twitter. Unsupported: ${unsupported.join(
                            ", "
                        )}`
                    );
                    return;
                }

                const orchestratorRunning = Boolean(runtime?.orchestrator?.running);
                const dryRunOn = Boolean(runtime?.dryRun);
                if (dryRunOn) {
                    const ok = window.confirm(
                        "DRY_RUN is ON. Facebook will NOT open and nothing will post. Continue anyway?"
                    );
                    if (!ok) return;
                }
                if (!orchestratorRunning) {
                    const ok = window.confirm(
                        "Orchestrator does not look like it's running. " +
                            "Approving now will NOT execute until you start START_BRAIN.bat. Continue anyway?"
                    );
                    if (!ok) return;
                } else {
                    const ok = window.confirm(
                        "This will approve and start posting immediately. " +
                            "A Playwright browser window should open on this machine. Continue?"
                    );
                    if (!ok) return;
                }
            }

            const res = await fetch("/api/social/post", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    content,
                    platforms: selectedPlatforms,
                    qwenPrompt,
                }),
            });
            const data = await res.json();
            if (!res.ok || !data.success) {
                throw new Error(data.error || "Failed to create post");
            }

            if (autoApprove) {
                const ids = Array.isArray(data.ids) ? (data.ids as string[]) : [];
                const failures: string[] = [];
                for (const id of ids) {
                    const approvalRes = await fetch(`/api/approvals/${id}`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ action: "approve" }),
                    });
                    const approvalData = await approvalRes.json();
                    if (!approvalRes.ok || !approvalData.success) {
                        failures.push(String(approvalData.error || id));
                    }
                }

                if (failures.length > 0) {
                    throw new Error(`Created post(s) but approval failed: ${failures.join(", ")}`);
                }

                const keepOpen = runtime?.facebook?.keepOpenSeconds ?? 0;
                const headless = runtime?.facebook?.headless ?? false;
                const browserHint = headless
                    ? "Headless is ON (no visible browser)."
                    : `A browser window should appear and stay open ~${keepOpen}s.`;

                setNotice(
                    `Approved and queued for execution. ${browserHint} ` +
                        "If you see a Facebook login page, log in manually; the session is saved in facebook_session."
                );
            } else {
                setNotice("Queued for approval. Go to Approvals to approve and execute.");
            }

            setContent("");
            setQwenPrompt("");
            setSelectedPlatforms([]);
            setShowModal(false);
            await fetchPosts();
        } catch (createError) {
            setError(createError instanceof Error ? createError.message : "Failed to create post");
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div>
                <div className="skeleton" style={{ height: 32, width: 200, marginBottom: 24 }} />
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 12 }}>
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="skeleton" style={{ height: 80, borderRadius: 12 }} />
                    ))}
                </div>
            </div>
        );
    }

    const connectedPlatforms = platforms.filter((platform) => platform.connected);
    const dryRunOn = Boolean(runtime?.dryRun);
    const orchestratorStatus = runtime?.orchestrator;
    const facebookRuntime = runtime?.facebook;
    const orchestratorLabel = orchestratorStatus?.running
        ? orchestratorStatus.ageSeconds != null
            ? `Running (last heartbeat ${orchestratorStatus.ageSeconds}s ago)`
            : "Running"
        : "Not running";

    return (
        <div>
            <div
                style={{
                    display: "flex",
                    alignItems: "flex-start",
                    justifyContent: "space-between",
                    flexWrap: "wrap",
                    gap: 16,
                    marginBottom: 24,
                }}
            >
                <div>
                    <h1
                        style={{
                            fontSize: 24,
                            fontWeight: 700,
                            color: "var(--text-primary)",
                            marginBottom: 4,
                        }}
                    >
                        Social Media
                    </h1>
                    <p style={{ fontSize: 14, color: "var(--text-muted)" }}>
                        Manage social posting and Qwen-driven Facebook automation
                    </p>
                </div>
                <button onClick={() => setShowModal(true)} className="btn btn-primary">
                    + Create Post
                </button>
            </div>

            {runtime && (
                <div
                    className="card"
                    style={{
                        marginBottom: 16,
                        padding: 14,
                        border: dryRunOn
                            ? "1px solid var(--danger)"
                            : orchestratorStatus && !orchestratorStatus.running
                              ? "1px solid var(--warning)"
                              : "1px solid var(--border-color)",
                        background: dryRunOn
                            ? "var(--danger-light)"
                            : orchestratorStatus && !orchestratorStatus.running
                              ? "var(--warning-light)"
                              : "var(--bg-secondary)",
                    }}
                >
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 10, alignItems: "center" }}>
                        <span className={`badge ${dryRunOn ? "badge-danger" : "badge-info"}`}>
                            DRY_RUN: {dryRunOn ? "ON" : "OFF"}
                        </span>
                        <span className={`badge ${orchestratorStatus?.running ? "badge-success" : "badge-warning"}`}>
                            Orchestrator: {orchestratorLabel}
                        </span>
                        {facebookRuntime && (
                            <span className="badge badge-secondary">
                                FB: headless={facebookRuntime.headless ? "true" : "false"}, keepOpen={
                                    facebookRuntime.keepOpenSeconds
                                }s, channel={facebookRuntime.browserChannel || "playwright-chromium"}
                            </span>
                        )}
                        {runtime?.reasoningEngine && (
                            <span className="badge badge-secondary">Brain: {runtime.reasoningEngine}</span>
                        )}
                    </div>
                    {dryRunOn && (
                        <div style={{ marginTop: 10, fontSize: 13, color: "var(--danger)" }}>
                            DRY_RUN is enabled. No browser will open and nothing will post.
                        </div>
                    )}
                    {orchestratorStatus && !orchestratorStatus.running && (
                        <div style={{ marginTop: 10, fontSize: 13, color: "var(--warning)" }}>
                            Orchestrator does not appear to be running. Start `START_BRAIN.bat` for approvals to execute.
                        </div>
                    )}
                    {notice && (
                        <div style={{ marginTop: 10, fontSize: 13, color: "var(--text-secondary)" }}>
                            {notice}
                        </div>
                    )}
                </div>
            )}

            <div
                style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                    gap: 12,
                    marginBottom: 24,
                }}
            >
                {platforms.map((platform) => {
                    const postCount = posts.filter((post) => post.platform === platform.id).length;
                    return (
                        <div
                            key={platform.id}
                            className="card"
                            style={{ display: "flex", alignItems: "center", gap: 12 }}
                        >
                            <div
                                style={{
                                    width: 36,
                                    height: 36,
                                    borderRadius: 8,
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    fontSize: 12,
                                    fontWeight: 700,
                                    background: "var(--bg-tertiary)",
                                }}
                            >
                                {platform.icon || platformIcon(platform.id)}
                            </div>
                            <div style={{ flex: 1 }}>
                                <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 2 }}>
                                    {platform.name}
                                </div>
                                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                                    {platform.connected
                                        ? `${postCount} post${postCount === 1 ? "" : "s"}`
                                        : platform.details || "Not connected"}
                                </div>
                            </div>
                            <span
                                className={`badge ${platform.connected ? "badge-success" : "badge-secondary"}`}
                                style={{ fontSize: 10 }}
                            >
                                {platform.connected ? "Ready" : "Setup"}
                            </span>
                        </div>
                    );
                })}
            </div>

            <div className="card" style={{ padding: 0, overflow: "hidden" }}>
                <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border-color)" }}>
                    <h2 style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>Recent Posts</h2>
                </div>

                {posts.length === 0 ? (
                    <div style={{ textAlign: "center", padding: 60 }}>
                        <h3
                            style={{
                                fontSize: 18,
                                fontWeight: 600,
                                color: "var(--text-primary)",
                                marginBottom: 8,
                            }}
                        >
                            No social posts yet
                        </h3>
                        <p style={{ fontSize: 14, color: "var(--text-muted)", marginBottom: 20 }}>
                            Create your first post from the dashboard.
                        </p>
                        <button onClick={() => setShowModal(true)} className="btn btn-primary">
                            + Create Post
                        </button>
                    </div>
                ) : (
                    <div>
                        {posts.map((post, index) => {
                            const createdDate = new Date(post.createdAt);
                            const now = new Date();
                            const diffMs = now.getTime() - createdDate.getTime();
                            const diffHours = Math.floor(diffMs / 3600000);
                            const diffDays = Math.floor(diffHours / 24);
                            const timeAgo =
                                diffDays > 0 ? `${diffDays}d ago` : diffHours > 0 ? `${diffHours}h ago` : "Just now";

                            return (
                                <div
                                    key={post.id}
                                    style={{
                                        padding: 20,
                                        borderTop: index > 0 ? "1px solid var(--border-color)" : "none",
                                    }}
                                >
                                    <div style={{ display: "flex", alignItems: "flex-start", gap: 12, marginBottom: 12 }}>
                                        <div
                                            style={{
                                                width: 30,
                                                height: 30,
                                                borderRadius: 7,
                                                display: "flex",
                                                alignItems: "center",
                                                justifyContent: "center",
                                                fontSize: 11,
                                                fontWeight: 700,
                                                background: "var(--bg-tertiary)",
                                            }}
                                        >
                                            {platformIcon(post.platform)}
                                        </div>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                                                <span
                                                    style={{
                                                        fontSize: 13,
                                                        fontWeight: 500,
                                                        textTransform: "capitalize",
                                                    }}
                                                >
                                                    {post.platform}
                                                </span>
                                                <span
                                                    className={`badge ${
                                                        post.status === "posted"
                                                            ? "badge-success"
                                                            : post.status === "approved"
                                                              ? "badge-info"
                                                              : "badge-warning"
                                                    }`}
                                                >
                                                    {post.status}
                                                </span>
                                                {post.brain && (
                                                    <span className="badge badge-secondary">
                                                        {post.brain}
                                                    </span>
                                                )}
                                                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{timeAgo}</span>
                                            </div>
                                            <p
                                                style={{
                                                    fontSize: 14,
                                                    lineHeight: 1.5,
                                                    color: "var(--text-secondary)",
                                                    margin: 0,
                                                    whiteSpace: "pre-wrap",
                                                }}
                                            >
                                                {post.content}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal" onClick={(event) => event.stopPropagation()}>
                        <div className="modal-header">
                            <h3 style={{ fontSize: 18, fontWeight: 600 }}>Create Social Post</h3>
                            <button onClick={() => setShowModal(false)} className="btn btn-ghost btn-icon btn-sm">
                                x
                            </button>
                        </div>

                        <div className="modal-body">
                            <div style={{ marginBottom: 16 }}>
                                <label
                                    style={{
                                        display: "block",
                                        fontSize: 13,
                                        fontWeight: 500,
                                        marginBottom: 8,
                                    }}
                                >
                                    Select Platforms
                                </label>
                                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                                    {connectedPlatforms.map((platform) => (
                                        <button
                                            key={platform.id}
                                            onClick={() => togglePlatform(platform.id)}
                                            className={`btn btn-sm ${
                                                selectedPlatforms.includes(platform.id)
                                                    ? "btn-primary"
                                                    : "btn-secondary"
                                            }`}
                                        >
                                            {platform.icon || platformIcon(platform.id)} {platform.name}
                                        </button>
                                    ))}
                                </div>
                                {connectedPlatforms.length === 0 && (
                                    <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 8 }}>
                                        No connected social platforms. Configure credentials and Facebook session first.
                                    </p>
                                )}
                            </div>

                            {facebookSelected && (
                                <div style={{ marginBottom: 16 }}>
                                    <label
                                        style={{
                                            display: "block",
                                            fontSize: 13,
                                            fontWeight: 500,
                                            marginBottom: 8,
                                        }}
                                    >
                                        Qwen Prompt (Required for Facebook)
                                    </label>
                                    <textarea
                                        value={qwenPrompt}
                                        onChange={(event) => setQwenPrompt(event.target.value)}
                                        className="input"
                                        rows={3}
                                        placeholder="Describe the post objective and audience..."
                                    />
                                    <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 8 }}>
                                        <button
                                            onClick={handleGenerateFacebookDraft}
                                            className="btn btn-secondary btn-sm"
                                            disabled={generating || !qwenPrompt.trim()}
                                        >
                                            {generating ? "Generating..." : "Generate with Qwen"}
                                        </button>
                                    </div>
                                </div>
                            )}

                            <div>
                                <label
                                    style={{
                                        display: "block",
                                        fontSize: 13,
                                        fontWeight: 500,
                                        marginBottom: 8,
                                    }}
                                >
                                    Content
                                </label>
                                <textarea
                                    value={content}
                                    onChange={(event) => setContent(event.target.value)}
                                    className="input"
                                    rows={6}
                                    placeholder={
                                        facebookSelected
                                            ? "Generate with Qwen or provide seed content..."
                                            : "What would you like to share?"
                                    }
                                    maxLength={characterLimit}
                                />
                                <div
                                    style={{
                                        fontSize: 12,
                                        color: "var(--text-muted)",
                                        marginTop: 4,
                                        textAlign: "right",
                                    }}
                                >
                                    {content.length}/{characterLimit}
                                </div>
                            </div>

                            {error && (
                                <div
                                    style={{
                                        marginTop: 12,
                                        padding: 10,
                                        borderRadius: 8,
                                        background: "var(--danger-light)",
                                        color: "var(--danger)",
                                        fontSize: 13,
                                    }}
                                >
                                    {error}
                                </div>
                            )}
                        </div>

                        <div className="modal-footer">
                            <button onClick={() => setShowModal(false)} className="btn btn-secondary">
                                Cancel
                            </button>
                            <button
                                onClick={() => handleCreatePost(false)}
                                disabled={submitting || !canSubmit}
                                className="btn btn-primary"
                            >
                                {submitting ? "Creating..." : "Queue for Approval"}
                            </button>
                            <button
                                onClick={() => handleCreatePost(true)}
                                disabled={submitting || !canSubmit}
                                className="btn btn-success"
                                title="Creates the post, approves it, and triggers immediate execution"
                            >
                                {submitting ? "Creating..." : "Approve & Post Now"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
