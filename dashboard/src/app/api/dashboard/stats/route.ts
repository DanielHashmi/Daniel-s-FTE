import { NextResponse } from "next/server";
import * as fs from "fs/promises";
import * as path from "path";

const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const VAULT_PATH = process.env.VAULT_PATH || path.join(PROJECT_ROOT, "AI_Employee_Vault");

export const dynamic = 'force-dynamic';

async function countFilesInFolder(folderPath: string): Promise<number> {
    try {
        const files = await fs.readdir(folderPath);
        return files.filter((f) => f.endsWith(".md")).length;
    } catch {
        return 0;
    }
}

async function getUptime(): Promise<string> {
    try {
        const statusFile = path.join(VAULT_PATH, ".fte_started");
        const startTime = await fs.readFile(statusFile, "utf-8");
        const start = new Date(startTime.trim());
        const diff = Date.now() - start.getTime();
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        return `${hours}h ${minutes}m`;
    } catch {
        return "0h 0m";
    }
}

export async function GET() {
    try {
        // Count pending approvals
        const pendingApprovals = await countFilesInFolder(path.join(VAULT_PATH, "Pending_Approval"));

        // Count all completed tasks
        const tasksToday = await countFilesInFolder(path.join(VAULT_PATH, "Done"));

        // Count active plans
        const plansActive = await countFilesInFolder(path.join(VAULT_PATH, "Plans"));

        // Count emails in Needs_Action
        let emailsProcessed = 0;
        try {
            const needsActionFiles = await fs.readdir(path.join(VAULT_PATH, "Needs_Action"));
            emailsProcessed = needsActionFiles.filter(f => f.includes("gmail") || f.includes("email")).length;
        } catch {
            emailsProcessed = 0;
        }

        // Count posts scheduled (in Pending_Approval)
        let postsScheduled = 0;
        try {
            const pendingFiles = await fs.readdir(path.join(VAULT_PATH, "Pending_Approval"));
            postsScheduled = pendingFiles.filter(f => f.startsWith("SOCIAL")).length;
        } catch {
            postsScheduled = 0;
        }

        const uptime = await getUptime();

        return NextResponse.json({
            pendingApprovals,
            tasksToday,
            emailsProcessed,
            postsScheduled,
            plansActive,
            uptime,
        }, {
            headers: {
                'Cache-Control': 'no-store, no-cache, must-revalidate',
                'Pragma': 'no-cache',
            }
        });
    } catch (error) {
        console.error("Failed to get dashboard stats:", error);
        return NextResponse.json({
            pendingApprovals: 0,
            tasksToday: 0,
            emailsProcessed: 0,
            postsScheduled: 0,
            plansActive: 0,
            uptime: "0h 0m",
        });
    }
}
