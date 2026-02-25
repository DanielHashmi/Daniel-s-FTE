import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import { listMarkdownFilesRecursive, VAULT_PATH } from "@/lib/vault";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    // Try to read the latest briefing from Briefings folder
    let briefingContent = "";
    let briefingDate = "";

    try {
      const briefingsPath = path.join(VAULT_PATH, "Briefings");
      const files = await fs.readdir(briefingsPath);
      const briefingFiles = files.filter((f) => f.endsWith("_Briefing.md")).sort().reverse();

      if (briefingFiles.length > 0) {
        const latestBriefing = path.join(briefingsPath, briefingFiles[0]);
        briefingContent = await fs.readFile(latestBriefing, "utf-8");
        briefingDate = briefingFiles[0].replace("_Monday_Briefing.md", "").replace("_Briefing.md", "");
      }
    } catch {
      // no briefing yet
    }

    const stats = {
      tasksCompleted: 0,
      emailsProcessed: 0,
      socialPosts: 0,
      approvalsPending: 0,
      revenue: 0,
      expenses: 0,
      timeSaved: "0h",
    };

    try {
      const doneFiles = await listMarkdownFilesRecursive("Done");
      const mdFiles = doneFiles.filter((f) => f.endsWith(".md"));
      stats.tasksCompleted = mdFiles.length;
      stats.emailsProcessed = mdFiles.filter((f) => /gmail|EMAIL/i.test(path.basename(f))).length;
      stats.socialPosts = mdFiles.filter((f) => /^SOCIAL/i.test(path.basename(f))).length;

      const minutesSaved = stats.tasksCompleted * 5;
      stats.timeSaved = minutesSaved >= 60 ? `${Math.floor(minutesSaved / 60)}h ${minutesSaved % 60}m` : `${minutesSaved}m`;
    } catch (error) {
      console.error("Error counting done tasks:", error);
    }

    try {
      stats.approvalsPending = (await listMarkdownFilesRecursive("Pending_Approval")).length;
    } catch (error) {
      console.error("Error counting pending approvals:", error);
    }

    try {
      const now = new Date();
      const monthDir = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
      const transactionsFile = path.join(VAULT_PATH, "Accounting", "transactions", monthDir, "transactions.json");

      const content = await fs.readFile(transactionsFile, "utf-8");
      const data = JSON.parse(content);

      if (data.transactions) {
        for (const txn of data.transactions) {
          if (txn.type === "income") stats.revenue += txn.amount;
          if (txn.type === "expense") stats.expenses += txn.amount;
        }
      }
    } catch {
      // no accounting yet
    }

    const activities = [];
    try {
      const doneFiles = (await listMarkdownFilesRecursive("Done")).slice(-10).reverse();
      for (const filePath of doneFiles) {
        const file = path.basename(filePath);
        let type: "email" | "social" | "system" = "system";
        let icon = "DOC";

        if (/gmail|EMAIL/i.test(file)) {
          type = "email";
          icon = "MAIL";
        } else if (/^SOCIAL/i.test(file)) {
          type = "social";
          icon = "SOCIAL";
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

    return NextResponse.json(
      {
        stats,
        activities,
        briefing: briefingContent,
        briefingDate,
        hasCustomBriefing: briefingContent.length > 0,
      },
      {
        headers: {
          "Cache-Control": "no-store, no-cache, must-revalidate",
          Pragma: "no-cache",
        },
      },
    );
  } catch (error) {
    console.error("Error getting briefing:", error);
    return NextResponse.json(
      {
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
        hasCustomBriefing: false,
      },
      { status: 500 },
    );
  }
}
