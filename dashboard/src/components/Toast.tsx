"use client";

import { useEffect } from "react";

interface ToastProps {
    message: string;
    type?: "success" | "error" | "info" | "warning";
    onClose: () => void;
    duration?: number;
}

export default function Toast({ message, type = "info", onClose, duration = 3000 }: ToastProps) {
    useEffect(() => {
        const timer = setTimeout(onClose, duration);
        return () => clearTimeout(timer);
    }, [onClose, duration]);

    const colors = {
        success: { bg: "var(--success-light)", border: "var(--success)", icon: "✓" },
        error: { bg: "var(--danger-light)", border: "var(--danger)", icon: "✕" },
        warning: { bg: "var(--warning-light)", border: "var(--warning)", icon: "⚠" },
        info: { bg: "var(--primary-light)", border: "var(--primary)", icon: "ℹ" }
    };

    const style = colors[type];

    return (
        <div style={{
            position: "fixed",
            bottom: 24,
            right: 24,
            zIndex: 9999,
            minWidth: 300,
            maxWidth: 500,
            padding: "16px 20px",
            background: style.bg,
            border: `1px solid ${style.border}`,
            borderRadius: 12,
            boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
            display: "flex",
            alignItems: "center",
            gap: 12,
            animation: "slideIn 0.3s ease-out"
        }}>
            <div style={{
                width: 24,
                height: 24,
                borderRadius: 12,
                background: style.border,
                color: "white",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 14,
                fontWeight: 600,
                flexShrink: 0
            }}>
                {style.icon}
            </div>
            <div style={{ flex: 1, fontSize: 14, color: style.border, fontWeight: 500 }}>
                {message}
            </div>
            <button
                onClick={onClose}
                style={{
                    background: "none",
                    border: "none",
                    color: style.border,
                    cursor: "pointer",
                    fontSize: 18,
                    padding: 4,
                    lineHeight: 1
                }}
            >
                ×
            </button>

            <style jsx>{`
                @keyframes slideIn {
                    from {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
            `}</style>
        </div>
    );
}
