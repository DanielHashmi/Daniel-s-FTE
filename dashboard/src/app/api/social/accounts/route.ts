import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";

const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const VAULT_PATH = path.join(PROJECT_ROOT, "AI_Employee_Vault");
const ENV_PATH = path.join(PROJECT_ROOT, ".env");

type AccountStatus = {
    id: string;
    name: string;
    icon: string;
    connected: boolean;
    details?: string;
};

function parseEnv(content: string): Record<string, string> {
    const env: Record<string, string> = {};
    for (const rawLine of content.split(/\r?\n/)) {
        const line = rawLine.trim();
        if (!line || line.startsWith("#") || !line.includes("=")) continue;
        const idx = line.indexOf("=");
        const key = line.slice(0, idx).trim();
        const value = line.slice(idx + 1).trim();
        env[key] = value;
    }
    return env;
}

export const dynamic = "force-dynamic";

export async function GET() {
    let envContent = "";
    try {
        envContent = await fs.readFile(ENV_PATH, "utf-8");
    } catch {
        // Continue with process env fallback
    }

    const parsedEnv = parseEnv(envContent);
    const getValue = (key: string): string =>
        parsedEnv[key] || process.env[key] || "";

    const facebookSessionDir = path.join(
        PROJECT_ROOT,
        getValue("FACEBOOK_SESSION_DIR") || "facebook_session"
    );

    const hasTwitter = Boolean(
        getValue("TWITTER_API_KEY") &&
        getValue("TWITTER_API_SECRET") &&
        getValue("TWITTER_ACCESS_TOKEN") &&
        getValue("TWITTER_ACCESS_TOKEN_SECRET")
    );

    const hasLinkedIn = Boolean(
        getValue("LINKEDIN_ACCESS_TOKEN") && getValue("LINKEDIN_AUTHOR_URN")
    );

    const hasFacebookConfig = Boolean(getValue("FACEBOOK_COMPOSER_URL"));
    const hasFacebookSession = await fs
        .access(facebookSessionDir)
        .then(() => true)
        .catch(() => false);

    const hasInstagram = Boolean(
        getValue("INSTAGRAM_ACCESS_TOKEN") && getValue("INSTAGRAM_BUSINESS_ID")
    );

    const accounts: AccountStatus[] = [
        {
            id: "twitter",
            name: "Twitter/X",
            icon: "X",
            connected: hasTwitter,
            details: hasTwitter ? "API credentials configured" : "Missing API credentials",
        },
        {
            id: "linkedin",
            name: "LinkedIn",
            icon: "IN",
            connected: hasLinkedIn,
            details: hasLinkedIn ? "API credentials configured" : "Missing access token/author URN",
        },
        {
            id: "facebook",
            name: "Facebook (Qwen + Playwright)",
            icon: "FB",
            connected: hasFacebookConfig && hasFacebookSession,
            details: hasFacebookConfig
                ? hasFacebookSession
                    ? "Composer URL + session ready"
                    : "Composer URL set; login session missing"
                : "Missing FACEBOOK_COMPOSER_URL",
        },
        {
            id: "instagram",
            name: "Instagram",
            icon: "IG",
            connected: hasInstagram,
            details: hasInstagram ? "Graph API credentials configured" : "Missing API credentials",
        },
    ];

    const heartbeatPath = path.join(VAULT_PATH, "Logs", "orchestrator_heartbeat.json");
    let orchestratorLastHeartbeat = "";
    let orchestratorRunning = false;
    let orchestratorAgeSeconds: number | null = null;
    try {
        const raw = await fs.readFile(heartbeatPath, "utf-8");
        const parsed = JSON.parse(raw) as { timestamp?: string };
        orchestratorLastHeartbeat = String(parsed.timestamp || "").trim();
        if (orchestratorLastHeartbeat) {
            const last = new Date(orchestratorLastHeartbeat).getTime();
            const ageMs = Date.now() - last;
            orchestratorAgeSeconds = Number.isFinite(ageMs) ? Math.max(0, Math.floor(ageMs / 1000)) : null;
            // A cycle can take longer than the poll interval (e.g., when running Qwen/Claude).
            // Consider it "running" if heartbeat was seen recently.
            orchestratorRunning = typeof orchestratorAgeSeconds === "number" && orchestratorAgeSeconds < 180;
        }
    } catch {
        // Heartbeat is optional; treat as unknown/offline.
    }

    // Fallback for older orchestrators: infer from runtime log modification time.
    if (!orchestratorRunning && !orchestratorLastHeartbeat) {
        const candidateLogs = [
            path.join(PROJECT_ROOT, "orchestrator_runtime.out.log"),
            path.join(PROJECT_ROOT, "orchestrator_runtime.log"),
        ];
        for (const candidate of candidateLogs) {
            try {
                const stat = await fs.stat(candidate);
                const ageMs = Date.now() - stat.mtimeMs;
                const ageSeconds = Math.max(0, Math.floor(ageMs / 1000));
                orchestratorAgeSeconds = ageSeconds;
                orchestratorLastHeartbeat = new Date(stat.mtimeMs).toISOString();
                orchestratorRunning = ageSeconds < 180;
                break;
            } catch {
                // Keep looking.
            }
        }
    }

    const parseBool = (raw: string): boolean => raw.toLowerCase() === "true";
    const parseIntSafe = (raw: string, fallback: number): number => {
        const n = Number.parseInt(raw, 10);
        return Number.isFinite(n) ? n : fallback;
    };

    return NextResponse.json({
        accounts,
        reasoningEngine: getValue("REASONING_ENGINE") || "qwen",
        dryRun: (getValue("DRY_RUN") || "false").toLowerCase() === "true",
        orchestrator: {
            running: orchestratorRunning,
            lastHeartbeat: orchestratorLastHeartbeat || null,
            ageSeconds: orchestratorAgeSeconds,
        },
        facebook: {
            composerUrl: getValue("FACEBOOK_COMPOSER_URL") || null,
            sessionDir: facebookSessionDir,
            browserChannel: (getValue("FACEBOOK_BROWSER_CHANNEL") || "").trim() || null,
            headless: parseBool(getValue("FACEBOOK_HEADLESS") || "false"),
            keepOpenSeconds: parseIntSafe(getValue("FACEBOOK_KEEP_OPEN_SECONDS") || "0", 0),
            loginWaitSeconds: parseIntSafe(getValue("FACEBOOK_LOGIN_WAIT_SECONDS") || "600", 600),
        },
    });
}
