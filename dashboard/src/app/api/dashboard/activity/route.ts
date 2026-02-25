import { NextResponse } from "next/server";
import * as fs from "fs/promises";
import * as path from "path";

const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const VAULT_PATH = process.env.VAULT_PATH || path.join(PROJECT_ROOT, "AI_Employee_Vault");

export const dynamic = 'force-dynamic';

interface ActivityItem {
    id: string;
    type: "email" | "social" | "approval" | "system";
    message: string;
    time: string;
}

async function getRecentActivity(): Promise<ActivityItem[]> {
    const activities: ActivityItem[] = [];

    try {
        // Check Done folder for recent completed tasks
        const donePath = path.join(VAULT_PATH, "Done");
        const doneFiles = await fs.readdir(donePath).catch(() => []);

        for (const file of doneFiles.slice(-5)) {
            const content = await fs.readFile(path.join(donePath, file), "utf-8").catch(() => "");
            const type = content.includes("email") ? "email" : content.includes("social") ? "social" : "system";

            activities.push({
                id: file,
                type,
                message: `Completed: ${file.replace(".md", "")}`,
                time: "Recently",
            });
        }

        // Check logs for recent activity
        const logsPath = path.join(VAULT_PATH, "logs");
        const logFiles = await fs.readdir(logsPath).catch(() => []);

        if (logFiles.length > 0) {
            const latestLog = logFiles.sort().pop();
            if (latestLog) {
                const logContent = await fs.readFile(path.join(logsPath, latestLog), "utf-8").catch(() => "");
                const lines = logContent.split("\n").filter((l) => l.trim()).slice(-10);

                for (const line of lines) {
                    try {
                        const log = JSON.parse(line);
                        activities.push({
                            id: `log-${Date.now()}-${Math.random()}`,
                            type: log.type || "system",
                            message: log.message || line,
                            time: log.timestamp || "Recently",
                        });
                    } catch {
                        // Not JSON, add as raw
                        activities.push({
                            id: `log-${Date.now()}-${Math.random()}`,
                            type: "system",
                            message: line.substring(0, 100),
                            time: "Recently",
                        });
                    }
                }
            }
        }
    } catch (error) {
        console.error("Failed to get activity:", error);
    }

    return activities.slice(-10);
}

export async function GET() {
    try {
        const items = await getRecentActivity();
        return NextResponse.json({ items });
    } catch {
        return NextResponse.json({ items: [] });
    }
}
