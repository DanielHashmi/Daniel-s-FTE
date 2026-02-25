"use client";

import { useState, useEffect, useCallback } from "react";
import Toast from "@/components/Toast";

interface EmailItem {
    id: string;
    from: string;
    subject: string;
    snippet: string;
    time: string;
    read: boolean;
    priority: string;
    tags?: string[];
    category?: string;
    requires_action?: boolean;
}

interface EmailDetail {
    id: string;
    filename: string;
    from: string;
    subject: string;
    body: string;
    timestamp: string;
    priority: string;
    folder: string;
    metadata: any;
    tags?: string[];
    category?: string;
    requires_action?: boolean;
}

interface ToastState {
    message: string;
    type: "success" | "error" | "info" | "warning";
}

export default function EmailPage() {
    const [emails, setEmails] = useState<EmailItem[]>([]);
    const [selectedEmail, setSelectedEmail] = useState<EmailDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [detailLoading, setDetailLoading] = useState(false);
    const [actionLoading, setActionLoading] = useState(false);
    const [showReplyModal, setShowReplyModal] = useState(false);
    const [replyContent, setReplyContent] = useState("");
    const [toast, setToast] = useState<ToastState | null>(null);
    const [activeFolder, setActiveFolder] = useState("Needs_Action");
    const [folderCounts, setFolderCounts] = useState<Record<string, number>>({});

    const showToast = (message: string, type: ToastState["type"] = "info") => {
        setToast({ message, type });
    };

    const fetchEmails = useCallback(async () => {
        try {
            const res = await fetch(`/api/email/inbox?t=${Date.now()}&folder=${activeFolder}`, { cache: 'no-store' });
            const data = await res.json();
            setEmails(data.emails || []);
            setFolderCounts(data.folderCounts || {});
        } catch (error) {
            console.error("Failed to fetch emails:", error);
            showToast("Failed to fetch emails", "error");
        } finally {
            setLoading(false);
        }
    }, [activeFolder]);

    useEffect(() => {
        fetchEmails();
        const interval = setInterval(fetchEmails, 10000);
        return () => clearInterval(interval);
    }, [fetchEmails]);

    const openEmail = async (emailId: string) => {
        setDetailLoading(true);
        try {
            const res = await fetch(`/api/email/${emailId}?t=${Date.now()}`, { cache: 'no-store' });

            if (!res.ok) {
                showToast("Email not found", "error");
                return;
            }

            const data = await res.json();
            setSelectedEmail(data);

            // Mark as read
            await fetch(`/api/email/${emailId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "mark_read" })
            });

            // Refresh list to update read status
            fetchEmails();
        } catch (error) {
            console.error("Failed to open email:", error);
            showToast("Failed to open email", "error");
        } finally {
            setDetailLoading(false);
        }
    };

    const moveEmail = async (targetFolder: string) => {
        if (!selectedEmail) return;

        setActionLoading(true);
        try {
            const res = await fetch(`/api/email/${selectedEmail.id}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "move", targetFolder })
            });

            const data = await res.json();
            if (data.success) {
                showToast(`Moved to ${targetFolder}`, "success");
                setSelectedEmail(null);
                fetchEmails();
            } else {
                showToast(data.error || "Failed to move email", "error");
            }
        } catch (error) {
            console.error("Failed to move email:", error);
            showToast("Failed to move email", "error");
        } finally {
            setActionLoading(false);
        }
    };

    const archiveEmail = async () => {
        if (!selectedEmail) return;

        setActionLoading(true);
        try {
            const res = await fetch(`/api/email/${selectedEmail.id}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "archive" })
            });

            const data = await res.json();
            if (data.success) {
                showToast("Email archived", "success");
                setSelectedEmail(null);
                fetchEmails();
            } else {
                showToast(data.error || "Failed to archive", "error");
            }
        } catch (error) {
            console.error("Failed to archive email:", error);
            showToast("Failed to archive email", "error");
        } finally {
            setActionLoading(false);
        }
    };

    const createReply = async () => {
        if (!selectedEmail || !replyContent.trim()) return;

        setActionLoading(true);
        try {
            const res = await fetch(`/api/email/${selectedEmail.id}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "create_reply", replyContent })
            });

            const data = await res.json();
            if (data.success) {
                showToast("Reply draft created in Pending Approval", "success");
                setShowReplyModal(false);
                setReplyContent("");
                setSelectedEmail(null);
                fetchEmails();
            } else {
                showToast(data.error || "Failed to create reply", "error");
            }
        } catch (error) {
            console.error("Failed to create reply:", error);
            showToast("Failed to create reply", "error");
        } finally {
            setActionLoading(false);
        }
    };

    const sendEmail = async () => {
        if (!selectedEmail) return;

        setActionLoading(true);
        try {
            const res = await fetch(`/api/email/send`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id: selectedEmail.id })
            });

            const data = await res.json();
            if (data.success) {
                showToast("Email sent successfully!", "success");
                setSelectedEmail(null);
                fetchEmails();
            } else {
                showToast(data.error || "Failed to send email", "error");
            }
        } catch (error) {
            console.error("Failed to send email:", error);
            showToast("Failed to send email", "error");
        } finally {
            setActionLoading(false);
        }
    };

    const formatTime = (timestamp: string) => {
        if (!timestamp) return "";
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffHours / 24);

        if (diffDays > 0) return `${diffDays}d ago`;
        if (diffHours > 0) return `${diffHours}h ago`;
        const diffMins = Math.floor(diffMs / 60000);
        if (diffMins > 0) return `${diffMins}m ago`;
        return "Just now";
    };

    if (loading) {
        return (
            <div>
                <div className="skeleton" style={{ height: 32, width: 200, marginBottom: 24 }} />
                <div className="skeleton" style={{ height: 400, borderRadius: 12 }} />
            </div>
        );
    }

    const folders = [
        { id: 'Needs_Action', label: 'Inbox', icon: '📥' },
        { id: 'Pending_Approval', label: 'Pending', icon: '⏳' },
        { id: 'Approved', label: 'Approved', icon: '✅' },
        { id: 'Done', label: 'Done', icon: '✓' },
        { id: 'Rejected', label: 'Rejected', icon: '❌' }
    ];

    return (
        <div>
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 16, marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>Email Management</h1>
                    <p style={{ fontSize: 14, color: "var(--text-muted)" }}>{emails.length} email{emails.length !== 1 ? 's' : ''} in {folders.find(f => f.id === activeFolder)?.label || 'folder'}</p>
                </div>
                <button onClick={fetchEmails} className="btn btn-secondary btn-sm">↻ Refresh</button>
            </div>

            {/* Filter Tabs */}
            <div style={{ display: "flex", gap: 8, marginBottom: 20, overflowX: "auto", paddingBottom: 8 }}>
                {folders.map(folder => {
                    const count = folderCounts[folder.id] || 0;
                    const isActive = activeFolder === folder.id;

                    return (
                        <button
                            key={folder.id}
                            onClick={() => setActiveFolder(folder.id)}
                            style={{
                                padding: "8px 16px",
                                borderRadius: 20,
                                border: `2px solid ${isActive ? "var(--primary)" : "var(--border-color)"}`,
                                background: isActive ? "var(--primary-light)" : "transparent",
                                fontSize: 13,
                                fontWeight: 500,
                                cursor: "pointer",
                                transition: "all 0.15s",
                                whiteSpace: "nowrap",
                                display: "flex",
                                alignItems: "center",
                                gap: 6,
                                color: isActive ? "var(--primary)" : "var(--text-secondary)"
                            }}
                        >
                            <span>{folder.icon}</span>
                            <span>{folder.label}</span>
                            {count > 0 && (
                                <span style={{
                                    background: isActive ? "var(--primary)" : "var(--bg-tertiary)",
                                    color: isActive ? "white" : "var(--text-muted)",
                                    padding: "2px 6px",
                                    borderRadius: 10,
                                    fontSize: 11,
                                    fontWeight: 600
                                }}>
                                    {count}
                                </span>
                            )}
                        </button>
                    );
                })}
            </div>

            {/* Email List */}
            <div className="card" style={{ padding: 0, overflow: "hidden" }}>
                {emails.length === 0 ? (
                    <div style={{ textAlign: "center", padding: 60 }}>
                        <div style={{ fontSize: 48, marginBottom: 16 }}>📭</div>
                        <h3 style={{ fontSize: 18, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>Inbox Empty</h3>
                        <p style={{ fontSize: 14, color: "var(--text-muted)" }}>No new emails to process</p>
                    </div>
                ) : (
                    emails.map((email, i) => (
                        <div
                            key={email.id}
                            onClick={() => openEmail(email.id)}
                            style={{
                                display: "flex", alignItems: "center", gap: 12, padding: "16px 20px",
                                borderTop: i > 0 ? "1px solid var(--border-color)" : "none",
                                cursor: "pointer", transition: "background 0.15s",
                                background: email.read ? undefined : "var(--bg-tertiary)"
                            }}
                            className="hover-bg"
                        >
                            <div style={{
                                width: 40, height: 40, borderRadius: 20,
                                background: email.priority === "high" ? "var(--danger-light)" : "var(--primary-light)",
                                display: "flex", alignItems: "center", justifyContent: "center",
                                fontSize: 16, fontWeight: 600,
                                color: email.priority === "high" ? "var(--danger)" : "var(--primary)",
                                flexShrink: 0
                            }}>
                                {email.from[0]?.toUpperCase() || "?"}
                            </div>
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4, flexWrap: "wrap" }}>
                                    <span style={{ fontSize: 14, fontWeight: email.read ? 500 : 600, color: "var(--text-primary)" }}>
                                        {email.subject}
                                    </span>
                                    {email.priority === "high" && (
                                        <span className="badge badge-danger" style={{ fontSize: 10 }}>High Priority</span>
                                    )}
                                    {email.requires_action && (
                                        <span className="badge badge-warning" style={{ fontSize: 10 }}>Action Required</span>
                                    )}
                                    {email.tags && email.tags.slice(0, 2).map(tag => (
                                        <span key={tag} className="badge badge-secondary" style={{ fontSize: 10 }}>
                                            {tag}
                                        </span>
                                    ))}
                                    {!email.read && (
                                        <div style={{
                                            width: 8, height: 8, borderRadius: 4,
                                            background: "var(--primary)"
                                        }} />
                                    )}
                                </div>
                                <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>{email.from}</div>
                                <div style={{ fontSize: 12, color: "var(--text-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                    {email.snippet}
                                </div>
                            </div>
                            <span style={{ fontSize: 12, color: "var(--text-muted)", flexShrink: 0 }}>
                                {formatTime(email.time)}
                            </span>
                        </div>
                    ))
                )}
            </div>

            {/* Email Detail Modal */}
            {selectedEmail && (
                <div style={{
                    position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", display: "flex",
                    alignItems: "center", justifyContent: "center", zIndex: 1000, padding: 20,
                    backdropFilter: "blur(4px)"
                }} onClick={() => setSelectedEmail(null)}>
                    <div className="card" style={{
                        maxWidth: 900, width: "100%", maxHeight: "90vh", display: "flex", flexDirection: "column",
                        boxShadow: "0 20px 60px rgba(0,0,0,0.3)"
                    }} onClick={e => e.stopPropagation()}>
                        {/* Header */}
                        <div style={{ padding: "20px 24px", borderBottom: "1px solid var(--border-color)", flexShrink: 0 }}>
                            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 12 }}>
                                <div style={{ flex: 1 }}>
                                    <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>{selectedEmail.subject}</h2>
                                    <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 8 }}>
                                        From: {selectedEmail.from}
                                    </div>
                                    <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
                                        {selectedEmail.priority === "high" && (
                                            <span className="badge badge-danger" style={{ fontSize: 10 }}>High Priority</span>
                                        )}
                                        {selectedEmail.requires_action && (
                                            <span className="badge badge-warning" style={{ fontSize: 10 }}>Action Required</span>
                                        )}
                                        {selectedEmail.category && (
                                            <span className="badge badge-info" style={{ fontSize: 10, textTransform: "capitalize" }}>
                                                {selectedEmail.category}
                                            </span>
                                        )}
                                        {selectedEmail.tags && selectedEmail.tags.map(tag => (
                                            <span key={tag} className="badge badge-secondary" style={{ fontSize: 10 }}>
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                                        {formatTime(selectedEmail.timestamp)} • Folder: {selectedEmail.folder}
                                    </div>
                                </div>
                                <button onClick={() => setSelectedEmail(null)} className="btn btn-ghost btn-icon">✕</button>
                            </div>
                        </div>

                        {/* Body */}
                        <div style={{ flex: 1, overflowY: "auto", padding: 24, background: "var(--bg-secondary)" }}>
                            {detailLoading ? (
                                <div className="skeleton" style={{ height: 200 }} />
                            ) : (
                                <div style={{ fontSize: 14, lineHeight: 1.6, whiteSpace: "pre-wrap", color: "var(--text-primary)" }}>
                                    {selectedEmail.body}
                                </div>
                            )}
                        </div>

                        {/* Actions */}
                        <div style={{ padding: "16px 24px", borderTop: "1px solid var(--border-color)", display: "flex", gap: 8, flexWrap: "wrap", flexShrink: 0 }}>
                            {/* Show Send button if in Approved folder */}
                            {selectedEmail.folder === "Approved" && (
                                <button
                                    onClick={sendEmail}
                                    disabled={actionLoading}
                                    className="btn btn-success"
                                >
                                    {actionLoading ? "Sending..." : "📤 Send Email"}
                                </button>
                            )}

                            {/* Show Reply button for incoming emails */}
                            {selectedEmail.folder === "Needs_Action" && !selectedEmail.body.includes("REPLY") && (
                                <button
                                    onClick={() => setShowReplyModal(true)}
                                    disabled={actionLoading}
                                    className="btn btn-primary"
                                >
                                    ✉️ Reply
                                </button>
                            )}

                            <button
                                onClick={archiveEmail}
                                disabled={actionLoading}
                                className="btn btn-secondary"
                            >
                                {actionLoading ? "Archiving..." : "📦 Archive"}
                            </button>

                            <div style={{ flex: 1 }} />

                            <select
                                onChange={(e) => e.target.value && moveEmail(e.target.value)}
                                disabled={actionLoading}
                                className="btn btn-secondary"
                                style={{ minWidth: 150, cursor: "pointer" }}
                                value=""
                            >
                                <option value="">Move to...</option>
                                {selectedEmail.folder !== "Needs_Action" && <option value="Needs_Action">📥 Inbox</option>}
                                {selectedEmail.folder !== "Pending_Approval" && <option value="Pending_Approval">📋 Pending Approval</option>}
                                {selectedEmail.folder !== "Approved" && <option value="Approved">✅ Approved</option>}
                                {selectedEmail.folder !== "Done" && <option value="Done">✓ Done</option>}
                                {selectedEmail.folder !== "Rejected" && <option value="Rejected">❌ Rejected</option>}
                            </select>
                        </div>
                    </div>
                </div>
            )}

            {/* Reply Modal */}
            {showReplyModal && selectedEmail && (
                <div style={{
                    position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", display: "flex",
                    alignItems: "center", justifyContent: "center", zIndex: 1001, padding: 20,
                    backdropFilter: "blur(4px)"
                }} onClick={() => !actionLoading && setShowReplyModal(false)}>
                    <div className="card" style={{ maxWidth: 700, width: "100%", padding: 0 }} onClick={e => e.stopPropagation()}>
                        {/* Header */}
                        <div style={{ padding: "20px 24px", borderBottom: "1px solid var(--border-color)" }}>
                            <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0 }}>Compose Reply</h2>
                        </div>

                        {/* Body */}
                        <div style={{ padding: 24 }}>
                            <div style={{ marginBottom: 16, padding: 12, background: "var(--bg-tertiary)", borderRadius: 8 }}>
                                <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>To:</div>
                                <div style={{ fontSize: 14, fontWeight: 500 }}>{selectedEmail.from}</div>
                            </div>

                            <div style={{ marginBottom: 16, padding: 12, background: "var(--bg-tertiary)", borderRadius: 8 }}>
                                <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>Subject:</div>
                                <div style={{ fontSize: 14, fontWeight: 500 }}>Re: {selectedEmail.subject}</div>
                            </div>

                            <div style={{ marginBottom: 16 }}>
                                <label style={{ fontSize: 13, fontWeight: 500, display: "block", marginBottom: 8 }}>
                                    Your Reply
                                </label>
                                <textarea
                                    value={replyContent}
                                    onChange={e => setReplyContent(e.target.value)}
                                    placeholder="Type your reply here..."
                                    style={{
                                        width: "100%", minHeight: 200, padding: 12, borderRadius: 8,
                                        border: "1px solid var(--border-color)", fontSize: 14, resize: "vertical",
                                        background: "var(--bg-secondary)", color: "var(--text-primary)",
                                        fontFamily: "inherit", lineHeight: 1.5
                                    }}
                                    autoFocus
                                />
                            </div>

                            <div style={{
                                padding: 12, background: "var(--info-light)", borderRadius: 8,
                                fontSize: 13, color: "var(--primary)", display: "flex", alignItems: "center", gap: 8
                            }}>
                                <span>ℹ️</span>
                                <span>Reply will be created as a draft in Pending Approval for your review before sending.</span>
                            </div>
                        </div>

                        {/* Footer */}
                        <div style={{ padding: "16px 24px", borderTop: "1px solid var(--border-color)", display: "flex", gap: 12, justifyContent: "flex-end" }}>
                            <button
                                onClick={() => { setShowReplyModal(false); setReplyContent(""); }}
                                className="btn btn-secondary"
                                disabled={actionLoading}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={createReply}
                                disabled={actionLoading || !replyContent.trim()}
                                className="btn btn-primary"
                            >
                                {actionLoading ? "Creating..." : "Create Draft"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Toast Notifications */}
            {toast && (
                <Toast
                    message={toast.message}
                    type={toast.type}
                    onClose={() => setToast(null)}
                />
            )}

            <style jsx>{`
                .hover-bg:hover { background: var(--bg-tertiary) !important; }
            `}</style>
        </div>
    );
}
