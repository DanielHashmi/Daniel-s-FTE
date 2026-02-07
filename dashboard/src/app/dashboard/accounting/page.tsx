"use client";

import { useState, useEffect, useCallback } from "react";

interface Transaction {
    id: string;
    type: "income" | "expense";
    description: string;
    amount: number;
    date: string;
}

interface Invoice {
    id: string;
    client: string;
    amount: number;
    status: "pending" | "paid" | "overdue";
    dueDate: string;
}

interface AccountingStats {
    revenue: number;
    expenses: number;
    pendingInvoices: number;
    overdueInvoices: number;
}

export default function AccountingPage() {
    const [stats, setStats] = useState<AccountingStats>({
        revenue: 0,
        expenses: 0,
        pendingInvoices: 0,
        overdueInvoices: 0,
    });
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchAccounting = useCallback(async () => {
        try {
            // Add cache-busting timestamp to prevent stale data
            const res = await fetch(`/api/odoo/summary?t=${Date.now()}`, {
                cache: 'no-store',
                headers: { 'Cache-Control': 'no-cache' }
            });
            const data = await res.json();
            setStats(data.stats || { revenue: 0, expenses: 0, pendingInvoices: 0, overdueInvoices: 0 });
            setTransactions(data.transactions || []);
            setInvoices(data.invoices || []);
        } catch (error) {
            console.error("Failed to fetch accounting:", error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAccounting();
        // Auto-sync every 10 seconds
        const interval = setInterval(fetchAccounting, 10000);
        return () => clearInterval(interval);
    }, [fetchAccounting]);

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(amount);
    };

    const handleSync = async () => {
        try {
            setLoading(true);
            const res = await fetch("/api/odoo/sync", { method: "POST" });
            const data = await res.json();
            if (data.success) {
                // Refresh data after sync
                await fetchAccounting();
            } else {
                console.error("Sync failed:", data.error);
            }
        } catch (error) {
            console.error("Sync error:", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div>
                <div className="skeleton" style={{ height: 32, width: 200, marginBottom: 24 }} />
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 24 }}>
                    {[1, 2, 3, 4].map(i => <div key={i} className="skeleton" style={{ height: 80, borderRadius: 12 }} />)}
                </div>
                <div className="skeleton" style={{ height: 300, borderRadius: 12 }} />
            </div>
        );
    }

    const statCards = [
        { label: "Revenue (MTD)", value: formatCurrency(stats.revenue), color: "var(--success)" },
        { label: "Expenses (MTD)", value: formatCurrency(stats.expenses), color: "var(--danger)" },
        { label: "Pending Invoices", value: stats.pendingInvoices.toString() },
        { label: "Overdue", value: stats.overdueInvoices.toString(), highlight: stats.overdueInvoices > 0 },
    ];

    return (
        <div>
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 16, marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>Accounting</h1>
                    <p style={{ fontSize: 14, color: "var(--text-muted)" }}>Financial overview and invoice management</p>
                </div>
                <button onClick={handleSync} className="btn btn-secondary btn-sm" disabled={loading}>
                    {loading ? "Syncing..." : "↻ Sync with Odoo"}
                </button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 12, marginBottom: 24 }}>
                {statCards.map((s, i) => (
                    <div key={i} className="stat-card" style={{ background: s.highlight ? "var(--danger-light)" : undefined }}>
                        <div style={{ fontSize: 12, color: s.highlight ? "var(--danger)" : "var(--text-muted)", marginBottom: 8 }}>{s.label}</div>
                        <div className="stat-value" style={{ color: s.color || (s.highlight ? "var(--danger)" : undefined) }}>{s.value}</div>
                    </div>
                ))}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 16 }} className="grid-2col">
                <div>
                    <h2 className="section-title" style={{ marginBottom: 12 }}>Recent Transactions</h2>
                    {transactions.length === 0 ? (
                        <div className="card" style={{ textAlign: "center", padding: 40 }}>
                            <div style={{ fontSize: 48, marginBottom: 16 }}>💰</div>
                            <h3 style={{ fontSize: 18, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>No transactions</h3>
                            <p style={{ fontSize: 14, color: "var(--text-muted)" }}>Connect Odoo to sync financial data</p>
                        </div>
                    ) : (
                        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
                            {transactions.map((t, i) => (
                                <div key={t.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: 16, borderTop: i > 0 ? "1px solid var(--border-color)" : "none" }}>
                                    <div style={{
                                        width: 40, height: 40, borderRadius: 8,
                                        background: t.type === "income" ? "var(--success-light)" : "var(--danger-light)",
                                        display: "flex", alignItems: "center", justifyContent: "center",
                                        color: t.type === "income" ? "var(--success)" : "var(--danger)",
                                        fontSize: 16, fontWeight: 600,
                                        flexShrink: 0
                                    }}>
                                        {t.type === "income" ? "↑" : "↓"}
                                    </div>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontSize: 14, fontWeight: 500, color: "var(--text-primary)" }}>{t.description}</div>
                                        <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{t.date}</div>
                                    </div>
                                    <span style={{ fontSize: 14, fontWeight: 600, color: t.type === "income" ? "var(--success)" : "var(--danger)" }}>
                                        {t.type === "income" ? "+" : "-"}{formatCurrency(Math.abs(t.amount))}
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div>
                    <h2 className="section-title" style={{ marginBottom: 12 }}>Invoices</h2>
                    {invoices.length === 0 ? (
                        <div className="card" style={{ textAlign: "center", padding: 40 }}>
                            <div style={{ fontSize: 48, marginBottom: 16 }}>📄</div>
                            <h3 style={{ fontSize: 18, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>No invoices</h3>
                            <p style={{ fontSize: 14, color: "var(--text-muted)" }}>Invoices from Odoo will appear here</p>
                        </div>
                    ) : (
                        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                            {invoices.map(inv => (
                                <div key={inv.id} className="card" style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                    <span style={{ fontSize: 24 }}>📄</span>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                            <span style={{ fontSize: 14, fontWeight: 500, color: "var(--text-primary)" }}>{inv.id}</span>
                                            <span className={`badge ${inv.status === "paid" ? "badge-success" : inv.status === "overdue" ? "badge-danger" : "badge-warning"}`}>
                                                {inv.status}
                                            </span>
                                        </div>
                                        <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{inv.client} • Due: {inv.dueDate}</div>
                                    </div>
                                    <span style={{ fontSize: 14, fontWeight: 600 }}>{formatCurrency(inv.amount)}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            <style jsx>{`
        @media (min-width: 768px) {
          .grid-2col { grid-template-columns: 1fr 1fr; }
        }
      `}</style>
        </div>
    );
}
