import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import matter from "gray-matter";
import {
  listMarkdownFilesRecursive,
  normalizeVaultRelative,
} from "@/lib/vault";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const folder = searchParams.get("folder") || "Needs_Action";

    const emails = [];
    const drafts = [];
    const folderCounts: Record<string, number> = {
      Needs_Action: 0,
      Pending_Approval: 0,
      Approved: 0,
      Done: 0,
      Rejected: 0,
    };

    const foldersToRead =
      folder === "all"
        ? ["Needs_Action", "Pending_Approval", "Approved", "Done", "Rejected"]
        : [folder];

    for (const currentFolder of foldersToRead) {
      const files = await listMarkdownFilesRecursive(currentFolder);
      let emailCount = 0;

      for (const filePath of files) {
        const file = path.basename(filePath);
        const isEmailByName =
          file.endsWith(".md") &&
          (file.startsWith("EMAIL") || file.startsWith("REPLY") || file.includes("gmail_watcher_email") || file.includes("_email"));

        if (!isEmailByName) continue;

        try {
          const content = await fs.readFile(filePath, "utf-8");
          const { data, content: body } = matter(content);
          if (!["email", "email_reply", "email_draft"].includes(String(data.type || ""))) continue;

          emailCount += 1;

          const sender = data.metadata?.sender || data.metadata?.to || data.from || data.to || "Unknown";
          const subject = data.metadata?.subject || data.subject || "No Subject";
          const rel = normalizeVaultRelative(filePath);
          const relFromFolder = rel.replace(new RegExp(`^${currentFolder}/`), "");
          const domain = relFromFolder.includes("/") ? relFromFolder.split("/")[0] : "general";

          emails.push({
            id: data.id || file.replace(".md", ""),
            from: sender,
            subject,
            snippet: body.substring(0, 200).replace(/^#.*\n/gm, "").trim(),
            time: data.timestamp || data.created || data.received || "",
            read: data.status === "read" || data.status === "processed",
            priority: data.priority || "normal",
            tags: data.metadata?.tags || [],
            category: data.metadata?.category || "notification",
            requires_action: data.metadata?.requires_action || false,
            folder: currentFolder,
            isReply: data.type === "email_reply" || file.startsWith("REPLY"),
            domain,
            path: rel,
          });
        } catch (error) {
          console.error(`Error processing email ${filePath}:`, error);
        }
      }

      folderCounts[currentFolder] = emailCount;
    }

    emails.sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime());

    // Drafts in Pending_Approval and Approved
    for (const draftFolder of ["Pending_Approval", "Approved"]) {
      const files = await listMarkdownFilesRecursive(draftFolder);
      for (const filePath of files) {
        const file = path.basename(filePath);
        if ((!file.startsWith("EMAIL") && !file.startsWith("DRAFT")) || !file.endsWith(".md")) continue;

        try {
          const content = await fs.readFile(filePath, "utf-8");
          const { data } = matter(content);
          if (data.action === "send_email" || data.type === "email_draft") {
            drafts.push({
              id: file.replace(".md", ""),
              to: data.to || "Unknown",
              subject: data.subject || "No Subject",
              status: draftFolder === "Pending_Approval" ? "pending" : draftFolder === "Approved" ? "approved" : "sent",
              domain: data.domain || "general",
            });
          }
        } catch (error) {
          console.error(`Error processing draft ${filePath}:`, error);
        }
      }
    }

    return NextResponse.json(
      { emails, drafts, folderCounts, _timestamp: Date.now() },
      {
        headers: {
          "Cache-Control": "no-store, no-cache, must-revalidate",
          Pragma: "no-cache",
        },
      },
    );
  } catch (error) {
    console.error("Error getting email inbox:", error);
    return NextResponse.json({ emails: [], drafts: [] }, { status: 500 });
  }
}
