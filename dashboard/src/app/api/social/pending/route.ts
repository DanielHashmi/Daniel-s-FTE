import { NextResponse } from "next/server";
import * as fs from "fs/promises";
import * as path from "path";

const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const VAULT_PATH = process.env.VAULT_PATH || path.join(PROJECT_ROOT, "AI_Employee_Vault");

export const dynamic = 'force-dynamic';

export async function GET() {
    try {
        const pendingPath = path.join(VAULT_PATH, "Pending_Approval");
        const files = await fs.readdir(pendingPath).catch(() => []);

        const posts = [];

        for (const file of files) {
            if (!file.includes("social") && !file.includes("post")) continue;
            if (!file.endsWith(".md")) continue;

            const content = await fs.readFile(path.join(pendingPath, file), "utf-8").catch(() => "");
            const stats = await fs.stat(path.join(pendingPath, file)).catch(() => null);

            // Extract platforms from content
            const platforms: string[] = [];
            if (content.toLowerCase().includes("twitter") || content.toLowerCase().includes("x.com")) platforms.push("twitter");
            if (content.toLowerCase().includes("facebook")) platforms.push("facebook");
            if (content.toLowerCase().includes("instagram")) platforms.push("instagram");
            if (content.toLowerCase().includes("linkedin")) platforms.push("linkedin");

            posts.push({
                id: file.replace(".md", ""),
                platforms: platforms.length > 0 ? platforms : ["twitter"],
                content: content.replace(/^#.*\n/, "").trim().substring(0, 500),
                status: "pending",
                createdAt: stats?.birthtime?.toLocaleString() || "Unknown",
            });
        }

        return NextResponse.json({ posts });
    } catch (error) {
        console.error("Failed to get pending posts:", error);
        return NextResponse.json({ posts: [] });
    }
}
