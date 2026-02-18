"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

interface SocialPost {
    id: string;
    platform: string;
    content: string;
    status: "pending" | "approved" | "posted" | "failed";
    createdAt: string;
    brain?: string;
    path?: string;
    sourceFolder?: string;
    domain?: string;
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
        method?: string;
        graphApiVersion?: string;
        composerUrl: string | null;
        sessionDir: string;
        browserChannel: string | null;
        headless: boolean;
        keepOpenSeconds: number;
        loginWaitSeconds: number;
    };
    instagram?: {
        method: string;
        graphApiVersion?: string;
        profileMode?: string;
        profileName?: string;
        profileFallbackToSession?: boolean;
        connectExistingBrowser?: boolean;
        cdpUrl?: string;
        cdpAutoStart?: boolean;
        cdpReachable?: boolean;
        composerUrl: string | null;
        sessionDir: string;
        hasSession: boolean;
        browserChannel: string | null;
        headless: boolean;
        keepOpenSeconds: number;
        loginWaitSeconds: number;
    };
    whatsapp?: {
        apiVersion?: string;
        phoneNumberId?: string | null;
        webhookDomain?: string;
        verifyTokenConfigured?: boolean;
    };
}

function platformIcon(platform: string): string {
    if (platform === "facebook") return "FB";
    if (platform === "twitter") return "X";
    if (platform === "linkedin") return "IN";
    if (platform === "instagram") return "IG";
    if (platform === "whatsapp") return "WA";
    return "SM";
}

const defaultPlatforms: PlatformStatus[] = [
    { id: "twitter", name: "Twitter/X", icon: "X", connected: false },
    { id: "linkedin", name: "LinkedIn", icon: "IN", connected: false },
    { id: "facebook", name: "Facebook", icon: "FB", connected: false },
    { id: "instagram", name: "Instagram", icon: "IG", connected: false },
    { id: "whatsapp", name: "WhatsApp (Cloud API)", icon: "WA", connected: false },
];

export default function SocialPage() {
    const [showModal, setShowModal] = useState(false);
    const [content, setContent] = useState("");
    const [qwenPrompt, setQwenPrompt] = useState("");
    const [instagramImageUrl, setInstagramImageUrl] = useState("");
    const [instagramHashtags, setInstagramHashtags] = useState("");
    const [whatsappTo, setWhatsappTo] = useState("");
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
        instagram?: AccountsResponse["instagram"];
        whatsapp?: AccountsResponse["whatsapp"];
    } | null>(null);

    const facebookSelected = selectedPlatforms.includes("facebook");
    const instagramSelected = selectedPlatforms.includes("instagram");
    const whatsappSelected = selectedPlatforms.includes("whatsapp");
    const twitterSelected = selectedPlatforms.includes("twitter");
    const characterLimit = facebookSelected || instagramSelected ? 2200 : twitterSelected ? 280 : whatsappSelected ? 4096 : 3000;

    const canSubmit = useMemo(() => {
        const hasAnyText = Boolean(content.trim() || qwenPrompt.trim());
        const facebookReady = !facebookSelected || Boolean(qwenPrompt.trim());
        const instagramReady = !instagramSelected || Boolean(instagramImageUrl.trim());
        const requiresDirectContent = selectedPlatforms.some(
            (platform) => !["facebook", "instagram"].includes(String(platform).toLowerCase())
        );
        const directContentReady = !requiresDirectContent || Boolean(content.trim());
        const whatsappReady = !whatsappSelected || Boolean(whatsappTo.trim());
        return selectedPlatforms.length > 0 && hasAnyText && facebookReady && instagramReady && directContentReady && whatsappReady;
    }, [selectedPlatforms, content, qwenPrompt, facebookSelected, instagramSelected, instagramImageUrl, whatsappSelected, whatsappTo]);

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
                instagram: data.instagram,
                whatsapp: data.whatsapp,
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

    const handleGenerateDraft = async () => {
        if (!qwenPrompt.trim()) {
            setError("Enter a Qwen prompt first.");
            return;
        }

        setGenerating(true);
        setError("");
        try {
            const route = instagramSelected && !facebookSelected
                ? "/api/social/instagram/generate"
                : "/api/social/facebook/generate";
            const res = await fetch(route, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    prompt: qwenPrompt,
                    seedContent: content,
                    seedCaption: content,
                }),
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
                    (p) => !["facebook", "twitter", "instagram", "linkedin", "whatsapp"].includes(String(p).toLowerCase())
                );
                if (unsupported.length > 0) {
                    setError(
                        `Approve & Post Now currently supports Facebook, Instagram, WhatsApp, Twitter, and LinkedIn. Unsupported: ${unsupported.join(
                            ", "
                        )}`
                    );
                    return;
                }

                const orchestratorRunning = Boolean(runtime?.orchestrator?.running);
                const dryRunOn = Boolean(runtime?.dryRun);
                const includesFacebook = selectedPlatforms.includes("facebook");
                if (dryRunOn) {
                    const ok = window.confirm(
                        "DRY_RUN is ON. No live social post will be sent. Continue anyway?"
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
                            (includesFacebook
                                ? "A Playwright browser window may open for Facebook. Continue?"
                                : "Continue?")
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
                    instagramImageUrl,
                    instagramHashtags,
                    whatsappTo,
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
                const facebookMethod = String(runtime?.facebook?.method || "playwright").toLowerCase();
                const browserHint = headless
                    ? "Headless is ON (no visible browser)."
                    : `A browser window should appear and stay open ~${keepOpen}s.`;
                const includesFacebook = selectedPlatforms.includes("facebook");
                const includesInstagram = selectedPlatforms.includes("instagram");
                const includesWhatsApp = selectedPlatforms.includes("whatsapp");
                const executionHints: string[] = [];
                if (includesFacebook) {
                    if (facebookMethod === "playwright") {
                        executionHints.push(
                            `${browserHint} If you see a Facebook login page, log in manually; the session is saved in facebook_session.`
                        );
                    } else {
                        executionHints.push(
                            `Facebook execution uses Graph API (${runtime?.facebook?.graphApiVersion || "configured version"}).`
                        );
                    }
                }
                if (includesInstagram) {
                    const igMode = String(runtime?.instagram?.method || "playwright").toLowerCase();
                    if (igMode === "playwright") {
                        const igHeadless = Boolean(runtime?.instagram?.headless);
                        const igKeepOpen = Number(runtime?.instagram?.keepOpenSeconds ?? 0);
                        const igProfileMode = String(runtime?.instagram?.profileMode || "session").toLowerCase();
                        const igProfileName = String(runtime?.instagram?.profileName || "Default");
                        const igFallback = Boolean(runtime?.instagram?.profileFallbackToSession);
                        const igAttachExisting = Boolean(runtime?.instagram?.connectExistingBrowser);
                        const igCdpUrl = String(runtime?.instagram?.cdpUrl || "http://127.0.0.1:9222");
                        const igCdpAutoStart = Boolean(runtime?.instagram?.cdpAutoStart);
                        const igCdpReachable = Boolean(runtime?.instagram?.cdpReachable);
                        const hasSavedIgSession = Boolean(runtime?.instagram?.hasSession);
                        const igHint = igHeadless
                            ? "Instagram Playwright is headless."
                            : `Instagram Playwright may open a browser and stay visible ~${igKeepOpen}s.`;
                        executionHints.push(
                            igAttachExisting
                                ? `${igHint} Instagram is configured to attach to your already-running browser (${igCdpUrl}) and post in that browser context.${
                                      igCdpReachable
                                          ? " CDP endpoint is reachable."
                                          : igCdpAutoStart
                                            ? " CDP endpoint is not reachable yet; the runner will try to start your default browser/profile in debug mode automatically."
                                            : " CDP endpoint is not reachable; start your default browser in debug mode first."
                                  }`
                                : igProfileMode === "system"
                                ? `${igHint} Instagram is configured to use your default browser profile (${igProfileName}).${
                                      igFallback
                                          ? " If default profile launch fails, it will automatically fall back to the saved instagram_session profile."
                                          : ""
                                  }`
                                : `${igHint} ${
                                      hasSavedIgSession
                                          ? "If Instagram asks for login again, complete it in the opened tab."
                                          : "No saved Instagram login session yet, so login in the opened tab on this first run."
                                  }`
                        );
                    } else {
                        executionHints.push("Instagram execution uses Graph API with your provided image URL.");
                    }
                }
                if (includesWhatsApp) {
                    executionHints.push(
                        `WhatsApp execution uses Cloud API (${runtime?.whatsapp?.apiVersion || "configured version"}) to ${whatsappTo.trim()}.`
                    );
                }
                const hintText = executionHints.length > 0 ? executionHints.join(" ") : "Execution has started.";

                setNotice(
                    `Approved and queued for execution. ${hintText}`
                );
            } else {
                setNotice("Queued for approval. Go to Approvals to approve and execute.");
            }

            setContent("");
            setQwenPrompt("");
            setInstagramImageUrl("");
            setInstagramHashtags("");
            setWhatsappTo("");
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
    const disconnectedPlatforms = platforms.filter((platform) => !platform.connected);
    const dryRunOn = Boolean(runtime?.dryRun);
    const orchestratorStatus = runtime?.orchestrator;
    const facebookRuntime = runtime?.facebook;
    const instagramRuntime = runtime?.instagram;
    const whatsappRuntime = runtime?.whatsapp;
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
                        Manage social posting with high-quality Qwen generation and MCP execution
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
                                FB: mode={facebookRuntime.method || "playwright"}, v={
                                    facebookRuntime.graphApiVersion || "v19.0"
                                }, headless={facebookRuntime.headless ? "true" : "false"}, keepOpen={
                                    facebookRuntime.keepOpenSeconds
                                }s
                            </span>
                        )}
                        {instagramRuntime && (
                            <span className="badge badge-secondary">
                                IG: mode={instagramRuntime.method}, headless={
                                    instagramRuntime.headless ? "true" : "false"
                                }, session={instagramRuntime.hasSession ? "yes" : "no"}, profile={
                                    instagramRuntime.profileMode || "session"
                                }, attachExisting={
                                    instagramRuntime.connectExistingBrowser ? "true" : "false"
                                }, cdp={
                                    instagramRuntime.connectExistingBrowser
                                        ? instagramRuntime.cdpReachable
                                            ? "online"
                                            : "offline"
                                        : "n/a"
                                }
                            </span>
                        )}
                        {runtime?.reasoningEngine && (
                            <span className="badge badge-secondary">Brain: {runtime.reasoningEngine}</span>
                        )}
                        {whatsappRuntime && (
                            <span className="badge badge-secondary">
                                WA: v={whatsappRuntime.apiVersion || "v19.0"}, phone={whatsappRuntime.phoneNumberId || "not set"}, webhookToken={
                                    whatsappRuntime.verifyTokenConfigured ? "set" : "missing"
                                }, inbox={whatsappRuntime.webhookDomain || "personal"}
                            </span>
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
                                    key={
                                        post.path ||
                                        `${post.id}__${post.status}__${post.createdAt || "unknown"}__${index}`
                                    }
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
                                                            : post.status === "failed"
                                                              ? "badge-danger"
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
                                    {platforms.map((platform) => (
                                        <button
                                            key={platform.id}
                                            onClick={() => {
                                                if (platform.connected) togglePlatform(platform.id);
                                            }}
                                            className={`btn btn-sm ${
                                                selectedPlatforms.includes(platform.id)
                                                    ? "btn-primary"
                                                    : "btn-secondary"
                                            }`}
                                            disabled={!platform.connected}
                                            title={
                                                platform.connected
                                                    ? `${platform.name} is ready`
                                                    : `${platform.name} setup required: ${platform.details || "missing credentials"}`
                                            }
                                            style={!platform.connected ? { opacity: 0.55, cursor: "not-allowed" } : undefined}
                                        >
                                            {platform.icon || platformIcon(platform.id)} {platform.name}
                                        </button>
                                    ))}
                                </div>
                                {connectedPlatforms.length === 0 && (
                                    <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 8 }}>
                                        No connected social platforms yet. Configure credentials in Settings first.
                                    </p>
                                )}
                                {disconnectedPlatforms.length > 0 && (
                                    <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 8 }}>
                                        Setup required:{" "}
                                        {disconnectedPlatforms.map((platform) => platform.name).join(", ")}
                                    </p>
                                )}
                            </div>

                            {(facebookSelected || instagramSelected) && (
                                <div style={{ marginBottom: 16 }}>
                                    <label
                                        style={{
                                            display: "block",
                                            fontSize: 13,
                                            fontWeight: 500,
                                            marginBottom: 8,
                                        }}
                                    >
                                        Qwen Prompt{facebookSelected ? " (Required for Facebook)" : ""}
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
                                            onClick={handleGenerateDraft}
                                            className="btn btn-secondary btn-sm"
                                            disabled={generating || !qwenPrompt.trim()}
                                        >
                                            {generating
                                                ? "Generating..."
                                                : instagramSelected && !facebookSelected
                                                  ? "Generate Instagram Caption"
                                                  : "Generate with Qwen"}
                                        </button>
                                    </div>
                                </div>
                            )}

                            {instagramSelected && (
                                <div style={{ marginBottom: 16, display: "grid", gap: 10 }}>
                                    <div>
                                        <label
                                            style={{
                                                display: "block",
                                                fontSize: 13,
                                                fontWeight: 500,
                                                marginBottom: 8,
                                            }}
                                        >
                                            Instagram Image URL (Required)
                                        </label>
                                        <input
                                            type="url"
                                            value={instagramImageUrl}
                                            onChange={(event) => setInstagramImageUrl(event.target.value)}
                                            className="input"
                                            placeholder="https://example.com/image.jpg"
                                        />
                                    </div>
                                    <div>
                                        <label
                                            style={{
                                                display: "block",
                                                fontSize: 13,
                                                fontWeight: 500,
                                                marginBottom: 8,
                                            }}
                                        >
                                            Optional Hashtags
                                        </label>
                                        <input
                                            value={instagramHashtags}
                                            onChange={(event) => setInstagramHashtags(event.target.value)}
                                            className="input"
                                            placeholder="#startup #productivity #smallbusiness"
                                        />
                                    </div>
                                </div>
                            )}

                            {whatsappSelected && (
                                <div style={{ marginBottom: 16 }}>
                                    <label
                                        style={{
                                            display: "block",
                                            fontSize: 13,
                                            fontWeight: 500,
                                            marginBottom: 8,
                                        }}
                                    >
                                        WhatsApp Recipient (E.164, Required)
                                    </label>
                                    <input
                                        type="tel"
                                        value={whatsappTo}
                                        onChange={(event) => setWhatsappTo(event.target.value)}
                                        className="input"
                                        placeholder="+15551234567"
                                    />
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
                                        facebookSelected || instagramSelected || whatsappSelected
                                            ? instagramSelected
                                                ? "Generate a high-quality caption with Qwen or type your own..."
                                                : whatsappSelected
                                                    ? "Write the WhatsApp message body..."
                                                    : "Generate with Qwen or provide seed content..."
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
