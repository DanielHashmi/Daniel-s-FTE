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

function normalizeDomain(raw: string): string {
    const value = String(raw || "").trim().toLowerCase();
    return value || "personal";
}

export const dynamic = "force-dynamic";

async function isOrchestratorPidRunning(lockPath: string): Promise<{ running: boolean; startedAt?: string }> {
    try {
        const raw = await fs.readFile(lockPath, "utf-8");
        const parsed = JSON.parse(raw) as { pid?: number; started_at?: string };
        const pid = Number(parsed.pid);
        if (!Number.isInteger(pid) || pid <= 0) {
            return { running: false };
        }
        try {
            // Signal 0 checks process existence without terminating it.
            process.kill(pid, 0);
            return {
                running: true,
                startedAt: parsed.started_at ? String(parsed.started_at) : undefined,
            };
        } catch {
            return { running: false };
        }
    } catch {
        return { running: false };
    }
}

async function isCdpReachable(cdpUrl: string): Promise<boolean> {
    const base = cdpUrl.replace(/\/+$/, "");
    const endpoint = `${base}/json/version`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 1200);
    try {
        const res = await fetch(endpoint, { cache: "no-store", signal: controller.signal });
        return res.ok;
    } catch {
        return false;
    } finally {
        clearTimeout(timer);
    }
}

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
    const instagramSessionDir = path.join(
        PROJECT_ROOT,
        getValue("INSTAGRAM_SESSION_DIR") || "instagram_session"
    );
    const instagramAuthMarker = path.join(instagramSessionDir, ".instagram_authenticated");

    const hasTwitter = Boolean(
        getValue("TWITTER_API_KEY") &&
        getValue("TWITTER_API_SECRET") &&
        getValue("TWITTER_ACCESS_TOKEN") &&
        getValue("TWITTER_ACCESS_TOKEN_SECRET")
    );

    const hasLinkedIn = Boolean(
        getValue("LINKEDIN_ACCESS_TOKEN") && getValue("LINKEDIN_AUTHOR_URN")
    );

    const facebookMethod = (getValue("FACEBOOK_POST_METHOD") || "graph_api").toLowerCase();
    const graphApiVersion = (getValue("META_GRAPH_API_VERSION") || "v19.0").trim();
    const hasFacebookGraphCreds = Boolean(
        getValue("FACEBOOK_PAGE_TOKEN") && getValue("FACEBOOK_PAGE_ID")
    );
    const hasFacebookConfig = Boolean(getValue("FACEBOOK_COMPOSER_URL"));
    const hasFacebookSession = await fs
        .access(facebookSessionDir)
        .then(() => true)
        .catch(() => false);
    const hasFacebook =
        facebookMethod === "playwright"
            ? hasFacebookConfig && hasFacebookSession
            : hasFacebookGraphCreds;

    const whatsappApiVersion = (getValue("WHATSAPP_API_VERSION") || graphApiVersion || "v19.0").trim();
    const whatsappPhoneNumberId = (getValue("WHATSAPP_PHONE_NUMBER_ID") || "").trim();
    const whatsappWebhookDomain = normalizeDomain(getValue("WHATSAPP_WEBHOOK_DOMAIN") || "personal");
    const hasWhatsAppVerifyToken = Boolean((getValue("WHATSAPP_VERIFY_TOKEN") || "").trim());
    const hasWhatsAppCloudConfig = Boolean(
        getValue("WHATSAPP_ACCESS_TOKEN") && whatsappPhoneNumberId
    );

    const instagramMethod = (getValue("INSTAGRAM_POST_METHOD") || "playwright").toLowerCase();
    const instagramComposerUrl = getValue("INSTAGRAM_COMPOSER_URL") || "https://www.instagram.com/";
    const instagramProfileMode = (getValue("INSTAGRAM_PROFILE_MODE") || "system").toLowerCase();
    const instagramProfileNameRaw = (getValue("INSTAGRAM_PROFILE_NAME") || "auto").trim() || "auto";
    const instagramProfileFallbackToSession =
        (getValue("INSTAGRAM_PROFILE_FALLBACK_TO_SESSION") || "true").toLowerCase() === "true";
    const instagramConnectExistingBrowser =
        (getValue("INSTAGRAM_CONNECT_EXISTING_BROWSER") || "false").toLowerCase() === "true";
    const instagramCdpUrl = (getValue("INSTAGRAM_CDP_URL") || "http://127.0.0.1:9222").trim();
    const instagramCdpAutoStart =
        (getValue("INSTAGRAM_CDP_AUTO_START") || "true").toLowerCase() === "true";
    const instagramCdpReachable = instagramConnectExistingBrowser
        ? await isCdpReachable(instagramCdpUrl)
        : false;
    const instagramProfileName =
        instagramProfileNameRaw.toLowerCase() === "auto"
            ? "last-used"
            : instagramProfileNameRaw;
    const hasInstagramGraphCreds = Boolean(
        getValue("INSTAGRAM_ACCESS_TOKEN") && getValue("INSTAGRAM_BUSINESS_ID")
    );
    const hasInstagramSessionDir = await fs
        .access(instagramSessionDir)
        .then(() => true)
        .catch(() => false);
    const hasInstagramAuthSession = await fs
        .access(instagramAuthMarker)
        .then(() => true)
        .catch(() => false);
    const hasInstagramPlaywrightConfig = Boolean(instagramComposerUrl);
    const hasInstagramSession =
        instagramMethod === "playwright" && instagramProfileMode === "system"
            ? true
            : hasInstagramAuthSession;
    const hasInstagram =
        instagramMethod === "playwright"
            ? hasInstagramPlaywrightConfig
            : hasInstagramGraphCreds;

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
            name: "Facebook",
            icon: "FB",
            connected: hasFacebook,
            details:
                facebookMethod === "playwright"
                    ? hasFacebookConfig
                        ? hasFacebookSession
                            ? "Playwright mode: composer URL + session ready"
                            : "Playwright mode: composer URL set; login session missing"
                        : "Playwright mode: missing FACEBOOK_COMPOSER_URL"
                    : hasFacebookGraphCreds
                      ? `Graph API mode: credentials configured (${graphApiVersion})`
                      : "Graph API mode: missing FACEBOOK_PAGE_TOKEN / FACEBOOK_PAGE_ID",
        },
        {
            id: "instagram",
            name: "Instagram",
            icon: "IG",
            connected: hasInstagram,
            details:
                instagramMethod === "playwright"
                    ? instagramConnectExistingBrowser
                        ? `Playwright mode: attach to existing browser via CDP (${instagramCdpUrl})${
                              instagramCdpReachable ? " [online]" : " [offline]"
                          }${instagramCdpAutoStart ? " (auto-start enabled)" : ""}`
                        : instagramProfileMode === "system"
                        ? `Playwright mode: using default browser profile (${instagramProfileName})${
                              instagramProfileFallbackToSession
                                  ? " with automatic session fallback"
                                  : ""
                          }`
                        : hasInstagramAuthSession
                          ? "Playwright mode: session ready"
                          : hasInstagramSessionDir
                            ? "Playwright mode: browser profile exists, login required"
                            : "Playwright mode: login required"
                    : hasInstagram
                      ? `Graph API credentials configured (${graphApiVersion})`
                      : "Missing INSTAGRAM_ACCESS_TOKEN / INSTAGRAM_BUSINESS_ID",
        },
        {
            id: "whatsapp",
            name: "WhatsApp (Cloud API)",
            icon: "WA",
            connected: hasWhatsAppCloudConfig,
            details: hasWhatsAppCloudConfig
                ? `Cloud API credentials configured (${whatsappApiVersion})${
                      hasWhatsAppVerifyToken ? ", webhook verify token set" : ", webhook verify token missing"
                  }`
                : "Missing WHATSAPP_ACCESS_TOKEN / WHATSAPP_PHONE_NUMBER_ID",
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

    // Final fallback: check lockfile PIDs directly to avoid false "not running" when heartbeat is stale.
    if (!orchestratorRunning) {
        const lockCandidates = [
            path.join(VAULT_PATH, "Logs", "orchestrator_local.lock"),
            path.join(VAULT_PATH, "Logs", "orchestrator_cloud.lock"),
        ];
        for (const lockPath of lockCandidates) {
            const state = await isOrchestratorPidRunning(lockPath);
            if (!state.running) continue;
            orchestratorRunning = true;
            if (!orchestratorLastHeartbeat && state.startedAt) {
                orchestratorLastHeartbeat = state.startedAt;
                const started = new Date(state.startedAt).getTime();
                const ageMs = Date.now() - started;
                orchestratorAgeSeconds = Number.isFinite(ageMs)
                    ? Math.max(0, Math.floor(ageMs / 1000))
                    : orchestratorAgeSeconds;
            }
            break;
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
            method: facebookMethod,
            graphApiVersion,
            composerUrl: getValue("FACEBOOK_COMPOSER_URL") || null,
            sessionDir: facebookSessionDir,
            browserChannel: (getValue("FACEBOOK_BROWSER_CHANNEL") || "").trim() || null,
            headless: parseBool(getValue("FACEBOOK_HEADLESS") || "false"),
            keepOpenSeconds: parseIntSafe(getValue("FACEBOOK_KEEP_OPEN_SECONDS") || "0", 0),
            loginWaitSeconds: parseIntSafe(getValue("FACEBOOK_LOGIN_WAIT_SECONDS") || "600", 600),
        },
        instagram: {
            method: instagramMethod,
            graphApiVersion,
            profileMode: instagramProfileMode,
            profileName: instagramProfileName,
            profileFallbackToSession: instagramProfileFallbackToSession,
            connectExistingBrowser: instagramConnectExistingBrowser,
            cdpUrl: instagramCdpUrl,
            cdpAutoStart: instagramCdpAutoStart,
            cdpReachable: instagramCdpReachable,
            composerUrl: instagramComposerUrl || null,
            sessionDir: instagramSessionDir,
            hasSession: hasInstagramSession,
            browserChannel: (getValue("INSTAGRAM_BROWSER_CHANNEL") || "").trim() || null,
            headless: parseBool(getValue("INSTAGRAM_HEADLESS") || "false"),
            keepOpenSeconds: parseIntSafe(getValue("INSTAGRAM_KEEP_OPEN_SECONDS") || "0", 0),
            loginWaitSeconds: parseIntSafe(getValue("INSTAGRAM_LOGIN_WAIT_SECONDS") || "600", 600),
        },
        whatsapp: {
            apiVersion: whatsappApiVersion,
            phoneNumberId: whatsappPhoneNumberId ? `...${whatsappPhoneNumberId.slice(-6)}` : null,
            webhookDomain: whatsappWebhookDomain,
            verifyTokenConfigured: hasWhatsAppVerifyToken,
        },
    });
}
