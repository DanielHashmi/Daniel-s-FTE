import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import {
  countMarkdownFilesRecursive,
  listMarkdownFilesRecursive,
  VAULT_PATH,
} from "@/lib/vault";

export const dynamic = "force-dynamic";

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
    const pendingApprovals = await countMarkdownFilesRecursive("Pending_Approval");
    const tasksToday = await countMarkdownFilesRecursive("Done");
    const plansActive = await countMarkdownFilesRecursive("Plans");

    let emailsProcessed = 0;
    const needsAction = await listMarkdownFilesRecursive("Needs_Action");
    emailsProcessed = needsAction.filter((p) => /email|gmail/i.test(path.basename(p))).length;

    const pending = await listMarkdownFilesRecursive("Pending_Approval");
    const postsScheduled = pending.filter((p) => /social/i.test(path.basename(p))).length;

    const uptime = await getUptime();

    return NextResponse.json(
      {
        pendingApprovals,
        tasksToday,
        emailsProcessed,
        postsScheduled,
        plansActive,
        uptime,
      },
      {
        headers: {
          "Cache-Control": "no-store, no-cache, must-revalidate",
          Pragma: "no-cache",
        },
      },
    );
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
