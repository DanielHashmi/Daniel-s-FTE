import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";

const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const VAULT_PATH = path.join(PROJECT_ROOT, "AI_Employee_Vault");

export const dynamic = 'force-dynamic';

export async function GET() {
    try {
        // Try to read the latest briefing from Briefings folder
        let briefingContent = "";
        let briefingDate = "";

        try {
            const briefingsPath = path.join(VAULT_PATH, "Briefings");
            const files = await fs.readdir(briefingsPath);
            const briefingFiles = files.filter(f => f.endsWith("_Briefing.md")).sort().reverse();

            if (briefingFiles.length > 0) {
                const latestBriefing = path.join(briefingsPath, briefingFiles[0]);
                briefingContent = await fs.readFile(latestBriefing, "utf-8");
                briefingDate = briefingFiles[0].replace("_Monday_Briefing.md", "").replace("_Briefing.md", "");
            }
        } catch (error) {
            console.log("No briefings found, generating from current data");
        }

        // Get real stats
        const stats = {
            tasksCompleted: 0,
            emailsProcessed: 0,
            socialPosts: 0,
            approvalsPending: 0,
            revenue: 0,
            expenses: 0,
            timeSaved: "0h",
        };

        // Count Done tasks
        try {
            const doneFiles = await fs.readdir(path.join(VAULT_PATH, "Done"));
            const mdFiles = doneFiles.filter(f => f.endsWith(".md"));
            stats.tasksCompleted = mdFiles.length;
            stats.emailsProcessed = mdFiles.filter(f => f.includes("gmail") || f.includes("EMAIL")).length;
            stats.socialPosts = mdFiles.filter(f => f.startsWith("SOCIAL")).length;

            // Calculate time saved (5 min per task)
            const minutesSaved = stats.tasksCompleted * 5;
            stats.timeSaved = minutesSaved >= 60
                ? `${Math.floor(minutesSaved / 60)}h ${minutesSaved % 60}m`
                : `${minutesSaved}m`;
        } catch (error) {
            console.error("Error counting done tasks:", error);
        }

        // Count pending approvals
        try {
            const pendingFiles = await fs.readdir(path.join(VAULT_PATH, "Pending_Approval"));
            stats.approvalsPending = pendingFiles.filter(f => f.endsWith(".md")).length;
        } catch (error) {
            console.error("Error counting pending approvals:", error);
        }

        // Get accounting data
        try {
            const now = new Date();
            const monthDir = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
            const transactionsFile = path.join(VAULT_PATH, "Accounting", "transactions", monthDir, "transactions.json");

            const content = await fs.readFile(transactionsFile, "utf-8");
            const data = JSON.parse(content);

            if (data.transactions) {
                for (const txn of data.transactions) {
                    if (txn.type === 'income') stats.revenue += txn.amount;
                    if (txn.type === 'expense') stats.expenses += txn.amount;
                }
            }
        } catch (error) {
            console.log("No accounting data found");
        }

        // Get recent activity
        const activities = [];
        try {
            const doneFiles = await fs.readdir(path.join(VAULT_PATH, "Done"));
            const recentFiles = doneFiles
                .filter(f => f.endsWith(".md"))
                .slice(-10)
                .reverse();

            for (const file of recentFiles) {
                let type: "email" | "social" | "system" = "system";
                let icon = "📄";

                if (file.includes("gmail") || file.includes("EMAIL")) {
                    type = "email";
                    icon = "✉️";
                } else if (file.startsWith("SOCIAL")) {
                    type = "social";
                    icon = "📱";
                }

                activities.push({
                    type,
                    icon,
                    title: file.replace(".md", "").replace(/_/g, " ").substring(0, 50),
                    time: "Recently",
                    status: "completed" as const,
                });
            }
        } catch (error) {
            console.error("Error reading recent activity:", error);
        }

        return NextResponse.json({
            stats,
            activities,
            briefing: briefingContent,
            briefingDate,
            hasCustomBriefing: briefingContent.length > 0
        }, {
            headers: {
                'Cache-Control': 'no-store, no-cache, must-revalidate',
                'Pragma': 'no-cache',
            }
        });
    } catch (error) {
        console.error("Error getting briefing:", error);
        return NextResponse.json({
            stats: {
                tasksCompleted: 0,
                emailsProcessed: 0,
                socialPosts: 0,
                approvalsPending: 0,
                revenue: 0,
                expenses: 0,
                timeSaved: "0h",
            },
            activities: [],
            briefing: "",
            briefingDate: "",
            hasCustomBriefing: false
        }, { status: 500 });
    }
}
