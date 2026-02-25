"use client";

import React, { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";

const navItems = [
    { href: "/dashboard", icon: "dashboard", label: "Dashboard" },
    { href: "/dashboard/fte", icon: "cpu", label: "FTE Control" },
    { href: "/dashboard/social", icon: "share", label: "Social Media" },
    { href: "/dashboard/email", icon: "mail", label: "Email" },
    { href: "/dashboard/approvals", icon: "check", label: "Approvals" },
    { href: "/dashboard/accounting", icon: "dollar", label: "Accounting" },
    { href: "/dashboard/briefing", icon: "chart", label: "CEO Briefing" },
    { href: "/dashboard/logs", icon: "list", label: "Logs" },
    { href: "/dashboard/settings", icon: "settings", label: "Settings" },
];

const icons: Record<string, React.ReactNode> = {
    dashboard: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>,
    cpu: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" /></svg>,
    share: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" /></svg>,
    mail: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>,
    check: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
    dollar: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
    chart: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>,
    list: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>,
    settings: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065zM15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>,
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [fteStatus, setFteStatus] = useState<"online" | "offline">("offline");
    const [theme, setTheme] = useState<"light" | "dark">("dark");
    const [mounted, setMounted] = useState(false);
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        setMounted(true);
        const stored = localStorage.getItem("theme");
        const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
        const t = stored ? (stored as "light" | "dark") : (prefersDark ? "dark" : "light");
        setTheme(t);
        document.documentElement.setAttribute("data-theme", t);
    }, []);

    useEffect(() => {
        const check = async () => {
            try {
                const res = await fetch("/api/fte/status");
                const data = await res.json();
                setFteStatus(data.running ? "online" : "offline");
            } catch { setFteStatus("offline"); }
        };
        check();
        const i = setInterval(check, 30000);
        return () => clearInterval(i);
    }, []);

    const toggleTheme = () => {
        const t = theme === "dark" ? "light" : "dark";
        setTheme(t);
        document.documentElement.setAttribute("data-theme", t);
        localStorage.setItem("theme", t);
    };

    const handleLogout = async () => {
        await fetch("/api/auth/logout", { method: "POST" });
        router.push("/");
    };

    if (!mounted) return null;

    return (
        <div style={{ display: "flex", minHeight: "100vh", background: "var(--bg-primary)" }}>
            {/* Overlay */}
            {sidebarOpen && (
                <div
                    onClick={() => setSidebarOpen(false)}
                    style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", zIndex: 40 }}
                />
            )}

            {/* Sidebar */}
            <aside
                style={{
                    width: 240,
                    background: "var(--bg-secondary)",
                    display: "flex",
                    flexDirection: "column",
                    position: "fixed",
                    top: 0,
                    left: 0,
                    bottom: 0,
                    zIndex: 50,
                    transform: sidebarOpen ? "translateX(0)" : "translateX(-100%)",
                    transition: "transform 0.2s ease",
                }}
                className="sidebar-desktop"
            >
                {/* Logo */}
                <div style={{ padding: 20 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        <div style={{ width: 40, height: 40, borderRadius: 10, background: "var(--bg-tertiary)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20 }}>
                            🤖
                        </div>
                        <div>
                            <div style={{ fontSize: 15, fontWeight: 600, color: "var(--text-primary)" }}>Daniel FTE</div>
                            <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 2 }}>
                                <span className={`status-dot ${fteStatus === "online" ? "status-online" : "status-offline"}`} />
                                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{fteStatus === "online" ? "Running" : "Stopped"}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Nav */}
                <nav style={{ flex: 1, padding: "0 12px", overflowY: "auto" }}>
                    <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                        {navItems.map((item) => (
                            <Link key={item.href} href={item.href} onClick={() => setSidebarOpen(false)} className={`nav-item ${pathname === item.href ? "active" : ""}`}>
                                {icons[item.icon]}
                                <span style={{ flex: 1 }}>{item.label}</span>
                                {item.href === "/dashboard/approvals" && <span className="badge badge-warning" style={{ fontSize: 10, height: 18, padding: "0 6px" }}>3</span>}
                            </Link>
                        ))}
                    </div>
                </nav>

                {/* Footer */}
                <div style={{ padding: 12 }}>
                    <button onClick={toggleTheme} className="btn btn-secondary" style={{ width: "100%", marginBottom: 12, justifyContent: "center" }}>
                        {theme === "dark" ? (
                            <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                        ) : (
                            <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" /></svg>
                        )}
                        {theme === "dark" ? "Light" : "Dark"}
                    </button>

                    <div style={{ display: "flex", alignItems: "center", gap: 10, padding: 10, background: "var(--bg-tertiary)", borderRadius: 10 }}>
                        <div style={{ width: 32, height: 32, borderRadius: "50%", background: "var(--accent)", color: "var(--bg-primary)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 600 }}>D</div>
                        <div style={{ flex: 1 }}>
                            <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text-primary)" }}>Daniel</div>
                        </div>
                        <button onClick={handleLogout} className="btn btn-ghost btn-sm btn-icon" title="Logout">
                            <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main content */}
            <div style={{ flex: 1, display: "flex", flexDirection: "column" }} className="main-content">
                {/* Mobile header */}
                <header className="mobile-header" style={{ display: "none", alignItems: "center", gap: 12, padding: 16, background: "var(--bg-secondary)" }}>
                    <button onClick={() => setSidebarOpen(true)} className="btn btn-ghost btn-icon">
                        <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" /></svg>
                    </button>
                    <span style={{ fontSize: 18 }}>🤖</span>
                    <span style={{ fontSize: 15, fontWeight: 600 }}>Daniel FTE</span>
                </header>

                {/* Page */}
                <main style={{ flex: 1, padding: 24, overflowY: "auto" }}>
                    {children}
                </main>
            </div>

            <style jsx global>{`
        @media (min-width: 1024px) {
          .sidebar-desktop {
            transform: translateX(0) !important;
          }
          .main-content {
            margin-left: 240px;
          }
        }
        @media (max-width: 1023px) {
          .mobile-header {
            display: flex !important;
          }
        }
      `}</style>
        </div>
    );
}
