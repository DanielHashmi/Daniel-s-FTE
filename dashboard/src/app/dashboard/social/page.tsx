"use client";

import { useState, useEffect, useCallback } from "react";

interface SocialPost {
    id: string;
    platform: string;
    content: string;
    status: "pending" | "approved" | "posted";
    createdAt: string;
}

interface PlatformStatus {
    id: string;
    name: string;
    icon: string;
    connected: boolean;
    account?: string;
}

export default function SocialPage() {
    const [showModal, setShowModal] = useState(false);
    const [content, setContent] = useState("");
    const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
    const [posts, setPosts] = useState<SocialPost[]>([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);

    const platforms: PlatformStatus[] = [
        { id: "twitter", name: "Twitter/X", icon: "🐦", connected: true, account: "@connected" },
        { id: "linkedin", name: "LinkedIn", icon: "💼", connected: false },
        { id: "facebook", name: "Facebook", icon: "📘", connected: false },
        { id: "instagram", name: "Instagram", icon: "📷", connected: false },
    ];

    const fetchPosts = useCallback(async () => {
        try {
            const res = await fetch(`/api/social/posts?t=${Date.now()}`, { cache: 'no-store' });
            const data = await res.json();
            let fetchedPosts = data.posts || [];

            // If no real posts, add realistic demo data
            if (fetchedPosts.length === 0) {
                fetchedPosts = [
                    {
                        id: "demo_1",
                        platform: "twitter",
                        content: "Excited to announce our AI Employee platform is live! Automating emails, social media, and business operations. 🚀 #AI #Automation",
                        status: "posted",
                        createdAt: new Date(Date.now() - 3600000).toISOString()
                    },
                    {
                        id: "demo_2",
                        platform: "facebook",
                        content: "Just launched our AI Employee system. It handles emails, monitors social media, and syncs with accounting - all automatically!",
                        status: "posted",
                        createdAt: new Date(Date.now() - 7200000).toISOString()
                    },
                    {
                        id: "demo_3",
                        platform: "instagram",
                        content: "Behind the scenes: AI Employee working 24/7 keeping your business running smoothly. From email responses to financial tracking ✨",
                        status: "posted",
                        createdAt: new Date(Date.now() - 86400000).toISOString()
                    }
                ];
            }

            setPosts(fetchedPosts);
        } catch (error) {
            console.error("Failed to fetch posts:", error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchPosts();
        // Auto-sync every 10 seconds
        const interval = setInterval(fetchPosts, 10000);
        return () => clearInterval(interval);
    }, [fetchPosts]);

    const togglePlatform = (id: string) => {
        setSelectedPlatforms(prev => prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]);
    };

    const handleCreatePost = async () => {
        if (!content.trim() || selectedPlatforms.length === 0) return;

        setSubmitting(true);
        try {
            const res = await fetch("/api/social/post", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ content, platforms: selectedPlatforms }),
            });

            if (res.ok) {
                setContent("");
                setSelectedPlatforms([]);
                setShowModal(false);
                fetchPosts();
            }
        } catch (error) {
            console.error("Failed to create post:", error);
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div>
                <div className="skeleton" style={{ height: 32, width: 200, marginBottom: 24 }} />
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 12 }}>
                    {[1, 2, 3, 4].map(i => <div key={i} className="skeleton" style={{ height: 80, borderRadius: 12 }} />)}
                </div>
            </div>
        );
    }

    return (
        <div>
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 16, marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>Social Media</h1>
                    <p style={{ fontSize: 14, color: "var(--text-muted)" }}>Manage posts and connected accounts</p>
                </div>
                <button onClick={() => setShowModal(true)} className="btn btn-primary">+ Create Post</button>
            </div>

            {/* Platform Status */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12, marginBottom: 24 }}>
                {platforms.map(p => {
                    const postCount = posts.filter(post => post.platform === p.id).length;
                    return (
                        <div key={p.id} className="card" style={{ display: "flex", alignItems: "center", gap: 12 }}>
                            <span style={{ fontSize: 28 }}>{p.icon}</span>
                            <div style={{ flex: 1 }}>
                                <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 2 }}>{p.name}</div>
                                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                                    {p.connected ? `${postCount} post${postCount !== 1 ? 's' : ''}` : "Not connected"}
                                </div>
                            </div>
                            <span className={`badge ${p.connected ? "badge-success" : "badge-secondary"}`} style={{ fontSize: 10 }}>
                                {p.connected ? "✓" : "Setup"}
                            </span>
                        </div>
                    );
                })}
            </div>

            {/* Posts List */}
            <div className="card" style={{ padding: 0, overflow: "hidden" }}>
                <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border-color)" }}>
                    <h2 style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>Recent Posts</h2>
                </div>
                {posts.length === 0 ? (
                    <div style={{ textAlign: "center", padding: 60 }}>
                        <div style={{ fontSize: 48, marginBottom: 16 }}>📱</div>
                        <h3 style={{ fontSize: 18, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>No posts yet</h3>
                        <p style={{ fontSize: 14, color: "var(--text-muted)", marginBottom: 20 }}>Create your first social media post</p>
                        <button onClick={() => setShowModal(true)} className="btn btn-primary">+ Create Post</button>
                    </div>
                ) : (
                    <div>
                        {posts.map((post, i) => {
                            const date = new Date(post.createdAt);
                            const now = new Date();
                            const diffMs = now.getTime() - date.getTime();
                            const diffHours = Math.floor(diffMs / 3600000);
                            const diffDays = Math.floor(diffHours / 24);
                            const timeAgo = diffDays > 0 ? `${diffDays}d ago` : diffHours > 0 ? `${diffHours}h ago` : "Just now";

                            return (
                                <div key={post.id} style={{
                                    padding: 20,
                                    borderTop: i > 0 ? "1px solid var(--border-color)" : "none"
                                }}>
                                    <div style={{ display: "flex", alignItems: "flex-start", gap: 12, marginBottom: 12 }}>
                                        <span style={{ fontSize: 24 }}>
                                            {post.platform === "twitter" ? "🐦" : post.platform === "facebook" ? "📘" : post.platform === "instagram" ? "📷" : "💼"}
                                        </span>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                                                <span style={{ fontSize: 13, fontWeight: 500, textTransform: "capitalize" }}>{post.platform}</span>
                                                <span className={`badge ${post.status === "posted" ? "badge-success" : post.status === "approved" ? "badge-info" : "badge-warning"}`}>
                                                    {post.status}
                                                </span>
                                                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{timeAgo}</span>
                                            </div>
                                            <p style={{ fontSize: 14, lineHeight: 1.5, color: "var(--text-secondary)", margin: 0 }}>
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
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 style={{ fontSize: 18, fontWeight: 600 }}>Create Post</h3>
                            <button onClick={() => setShowModal(false)} className="btn btn-ghost btn-icon btn-sm">✕</button>
                        </div>
                        <div className="modal-body">
                            <div style={{ marginBottom: 16 }}>
                                <label style={{ display: "block", fontSize: 13, fontWeight: 500, marginBottom: 8 }}>Select Platforms</label>
                                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                                    {platforms.filter(p => p.connected).map(p => (
                                        <button
                                            key={p.id}
                                            onClick={() => togglePlatform(p.id)}
                                            className={`btn btn-sm ${selectedPlatforms.includes(p.id) ? "btn-primary" : "btn-secondary"}`}
                                        >
                                            {p.icon} {p.name}
                                        </button>
                                    ))}
                                </div>
                                {platforms.filter(p => p.connected).length === 0 && (
                                    <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 8 }}>No platforms connected. Configure credentials in Settings.</p>
                                )}
                            </div>
                            <div>
                                <label style={{ display: "block", fontSize: 13, fontWeight: 500, marginBottom: 8 }}>Content</label>
                                <textarea
                                    value={content}
                                    onChange={e => setContent(e.target.value)}
                                    className="input"
                                    rows={5}
                                    placeholder="What would you like to share?"
                                    maxLength={280}
                                />
                                <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4, textAlign: "right" }}>{content.length}/280</div>
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button onClick={() => setShowModal(false)} className="btn btn-secondary">Cancel</button>
                            <button
                                onClick={handleCreatePost}
                                disabled={submitting || !content.trim() || selectedPlatforms.length === 0}
                                className="btn btn-primary"
                            >
                                {submitting ? "Creating..." : "Create Post (Requires Approval)"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
