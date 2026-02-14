import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";

const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const ENV_PATH = path.join(PROJECT_ROOT, ".env");

export async function GET() {
    try {
        const envContent = await fs.readFile(ENV_PATH, "utf-8");
        const settings: {
            dryRun: boolean;
            hitl: boolean;
            gmailInterval: number;
            socialInterval: number;
        } = {
            dryRun: false,
            hitl: true,
            gmailInterval: 60,
            socialInterval: 300,
        };

        const integrations: Array<{id: string; name: string; icon: string; connected: boolean; envKey: string}> = [];

        // Parse .env file
        const lines = envContent.split("\n");
        for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith("#") || !trimmed.includes("=")) continue;

            const [key, value] = trimmed.split("=");

            if (key === "DRY_RUN") settings.dryRun = value === "true";
            if (key === "REQUIRE_EMAIL_APPROVAL") settings.hitl = value === "true";
            if (key === "GMAIL_INTERVAL") settings.gmailInterval = parseInt(value) || 60;
            if (key === "LINKEDIN_INTERVAL") settings.socialInterval = parseInt(value) || 300;

            // Check integrations
            if (key.includes("TWITTER") && value && value.length > 5) {
                if (!integrations.find(i => i.id === "twitter")) {
                    integrations.push({
                        id: "twitter",
                        name: "Twitter/X",
                        icon: "🐦",
                        connected: true,
                        envKey: "TWITTER_API_KEY"
                    });
                }
            }

            if (key.includes("LINKEDIN") && value && value.length > 5) {
                if (!integrations.find(i => i.id === "linkedin")) {
                    integrations.push({
                        id: "linkedin",
                        name: "LinkedIn",
                        icon: "💼",
                        connected: true,
                        envKey: "LINKEDIN_ACCESS_TOKEN"
                    });
                }
            }

            if (key.includes("FACEBOOK") && value && value.length > 5) {
                if (!integrations.find(i => i.id === "facebook")) {
                    integrations.push({
                        id: "facebook",
                        name: "Facebook",
                        icon: "FB",
                        connected: true,
                        envKey: "FACEBOOK_COMPOSER_URL"
                    });
                }
            }

            if (key.includes("ODOO") && value && value.length > 5) {
                if (!integrations.find(i => i.id === "odoo")) {
                    integrations.push({
                        id: "odoo",
                        name: "Odoo",
                        icon: "🔷",
                        connected: true,
                        envKey: "ODOO_URL"
                    });
                }
            }

            if (key.includes("GMAIL") && value && value.length > 5) {
                if (!integrations.find(i => i.id === "gmail")) {
                    integrations.push({
                        id: "gmail",
                        name: "Gmail",
                        icon: "📧",
                        connected: true,
                        envKey: "GMAIL_CREDENTIALS"
                    });
                }
            }
        }

        return NextResponse.json({ settings, integrations });
    } catch (error) {
        console.error("Error reading settings:", error);
        return NextResponse.json({
            settings: { dryRun: true, hitl: true, gmailInterval: 60, socialInterval: 300 },
            integrations: []
        }, { status: 500 });
    }
}

export async function PATCH(request: Request) {
    try {
        const updates = await request.json();
        const envContent = await fs.readFile(ENV_PATH, "utf-8");
        const lines = envContent.split("\n");

        // Update specific values
        for (const [key, value] of Object.entries(updates)) {
            let envKey = "";

            if (key === "dryRun") envKey = "DRY_RUN";
            else if (key === "hitl") envKey = "REQUIRE_EMAIL_APPROVAL";
            else continue;

            const lineIndex = lines.findIndex(l => l.trim().startsWith(`${envKey}=`));
            if (lineIndex >= 0) {
                lines[lineIndex] = `${envKey}=${value}`;
            } else {
                lines.push(`${envKey}=${value}`);
            }
        }

        await fs.writeFile(ENV_PATH, lines.join("\n"));

        return NextResponse.json({ success: true });
    } catch (error) {
        console.error("Error updating settings:", error);
        return NextResponse.json({ success: false, error: "Failed to update settings" }, { status: 500 });
    }
}
