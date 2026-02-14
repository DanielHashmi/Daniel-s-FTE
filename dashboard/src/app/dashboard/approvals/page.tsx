"use client";

import { useState, useEffect, useCallback } from "react";

interface Approval {
    id: string;
    title: string;
    type: string;
    content: string;
    priority: string;
    timestamp: string;
    action?: string;
    platform?: string;
}

export default function ApprovalsPage() {
    const [approvals, setApprovals] = useState<Approval[]>([]);
    const [selectedApproval, setSelectedApproval] = useState<Approval | null>(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);

    const fetchApprovals = useCallback(async () => {
        try {
            const res = await fetch(`/api/approvals?t=${Date.now()}`, {
                cache: 'no-store'
            });
            const data = await res.json();
            setApprovals(data.approvals || []);
        } catch (error) {
            console.error("Failed to fetch approvals:", error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchApprovals();
        // Auto-sync every 10 seconds for real-time updates
        const interval = setInterval(fetchApprovals, 10000);
        return () => clearInterval(interval);
    }, [fetchApprovals]);

    const handleAction = async (
        approval: Approval,
        action: "approve" | "reject",
        autoSend: boolean = false
    ) => {
        setActionLoading(true);
        try {
            const res = await fetch(`/api/approvals/${approval.id}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action }),
            });

            const data = await res.json();

            if (data.success) {
                // If approved and it's an email reply, optionally send it
                if (action === "approve" && autoSend && approval.type?.includes("email")) {
                    // Trigger send
                    const sendRes = await fetch(`/api/email/send`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ id: approval.id })
                    });

                    const sendData = await sendRes.json();
                    if (sendData.success) {
                        alert("Approved and sent successfully!");
                    } else {
                        alert(`Approved but send failed: ${sendData.error}`);
                    }
                } else {
                    const platform = String(approval.platform || "").toLowerCase();
                    if (action === "approve" && approval.type === "social" && platform === "facebook") {
                        alert(
                            "Approved. Facebook automation is executing now.\n\n" +
                                "You should see a Playwright browser window open on this machine. " +
                                "If a Facebook login page appears, log in manually; the session is saved under facebook_session."
                        );
                    } else {
                        alert(`${action === "approve" ? "Approved" : "Rejected"} successfully`);
                    }
                }
            }

            setSelectedApproval(null);
            fetchApprovals();
        } catch (error) {
            console.error(`Failed to ${action}:`, error);
            alert(`Failed to ${action}`);
        } finally {
            setActionLoading(false);
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

    return (
        <div>
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 16, marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>Approvals</h1>
                    <p style={{ fontSize: 14, color: "var(--text-muted)" }}>{approvals.length} items pending review</p>
                </div>
                <button onClick={fetchApprovals} className="btn btn-secondary btn-sm">Refresh</button>
            </div>

            {approvals.length === 0 ? (
                <div className="card" style={{ textAlign: "center", padding: 60 }}>
                    <div style={{ fontSize: 40, marginBottom: 16, fontWeight: 700 }}>OK</div>
                    <h3 style={{ fontSize: 20, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>All caught up!</h3>
                    <p style={{ fontSize: 14, color: "var(--text-muted)" }}>No pending approvals at the moment</p>
                </div>
            ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    {approvals.map(approval => (
                        <div key={approval.id} className="card" style={{ display: "flex", alignItems: "center", gap: 12 }}>
                            <span style={{ fontSize: 28 }}>
                                {approval.type === "social" ? "SOC" : approval.type === "email" ? "MAIL" : "DOC"}
                            </span>
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                                    <span style={{ fontSize: 15, fontWeight: 500, color: "var(--text-primary)" }}>{approval.title}</span>
                                    {approval.priority === "high" && <span className="badge badge-danger">Urgent</span>}
                                    <span className="badge badge-info">{approval.type}</span>
                                </div>
                                <p style={{ fontSize: 13, color: "var(--text-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                    {approval.content.substring(0, 150)}...
                                </p>
                                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{approval.timestamp}</span>
                            </div>
                            <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
                                <button onClick={() => setSelectedApproval(approval)} className="btn btn-secondary btn-sm">View</button>
                                <button
                                    onClick={() => handleAction(approval, "approve")}
                                    disabled={actionLoading}
                                    className="btn btn-success btn-sm"
                                >
                                    Approve
                                </button>
                                <button
                                    onClick={() => handleAction(approval, "reject")}
                                    disabled={actionLoading}
                                    className="btn btn-danger btn-sm"
                                >
                                    Reject
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {selectedApproval && (
                <div className="modal-overlay" onClick={() => setSelectedApproval(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 style={{ fontSize: 18, fontWeight: 600 }}>{selectedApproval.title}</h3>
                            <button onClick={() => setSelectedApproval(null)} className="btn btn-ghost btn-icon btn-sm">x</button>
                        </div>
                        <div className="modal-body">
                            <div style={{ marginBottom: 16 }}>
                                <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>Type</div>
                                <span className="badge badge-info">{selectedApproval.type}</span>
                            </div>
                            <div style={{ marginBottom: 16 }}>
                                <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>Content</div>
                                <div style={{ whiteSpace: "pre-wrap", fontSize: 13, lineHeight: 1.6 }}>{selectedApproval.content}</div>
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button
                                onClick={() => {
                                    handleAction(selectedApproval, "reject", false);
                                }}
                                disabled={actionLoading}
                                className="btn btn-danger"
                            >
                                Reject
                            </button>
                            {selectedApproval.type?.includes("email") ? (
                                <>
                                    <button
                                        onClick={() => {
                                            handleAction(selectedApproval, "approve", false);
                                        }}
                                        disabled={actionLoading}
                                        className="btn btn-secondary"
                                    >
                                        Approve (Do Not Send)
                                    </button>
                                    <button
                                        onClick={() => {
                                            handleAction(selectedApproval, "approve", true);
                                        }}
                                        disabled={actionLoading}
                                        className="btn btn-success"
                                    >
                                        Approve & Send
                                    </button>
                                </>
                            ) : (
                                <button
                                    onClick={() => {
                                        handleAction(selectedApproval, "approve", false);
                                    }}
                                    disabled={actionLoading}
                                    className="btn btn-success"
                                >
                                    Approve
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
