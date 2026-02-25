import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import matter from "gray-matter";
import { VAULT_PATH, listMarkdownFilesRecursive } from "@/lib/vault";

export const dynamic = "force-dynamic";

type LocatedEmail = {
  folder: string;
  filePath: string;
  fileName: string;
  relativeInFolder: string;
  frontmatter: Record<string, any>;
  body: string;
};

async function findEmailById(id: string): Promise<LocatedEmail | null> {
  const folders = ["Needs_Action", "Pending_Approval", "Approved", "Rejected", "Done"];

  for (const folder of folders) {
    const files = await listMarkdownFilesRecursive(folder);
    for (const filePath of files) {
      if (!filePath.toLowerCase().endsWith(".md")) continue;

      try {
        const raw = await fs.readFile(filePath, "utf-8");
        const parsed = matter(raw);
        const data = (parsed.data || {}) as Record<string, any>;
        const fileName = path.basename(filePath);
        const relativeInFolder = path.relative(path.join(VAULT_PATH, folder), filePath);

        const candidates = [
          String(data.id || ""),
          fileName.replace(/\.md$/i, ""),
          relativeInFolder.replace(/\.md$/i, "").split(path.sep).join("__"),
        ];

        if (candidates.includes(id)) {
          return {
            folder,
            filePath,
            fileName,
            relativeInFolder,
            frontmatter: data,
            body: parsed.content,
          };
        }
      } catch {
        continue;
      }
    }
  }

  return null;
}

function resolveDomainFromRelative(relativeInFolder: string): string {
  const normalized = relativeInFolder.split(path.sep).join("/");
  return normalized.includes("/") ? normalized.split("/")[0] : "general";
}

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { id } = await params;
    const located = await findEmailById(id);
    if (!located) {
      return NextResponse.json({ error: "Email not found" }, { status: 404 });
    }

    const data = located.frontmatter;
    const domain = data.domain || resolveDomainFromRelative(located.relativeInFolder);

    return NextResponse.json(
      {
        id: data.id || located.fileName.replace(".md", ""),
        filename: located.fileName,
        from: data.metadata?.sender || data.from || "Unknown",
        subject: data.metadata?.subject || data.subject || "No Subject",
        body: located.body.trim(),
        timestamp: data.timestamp || "",
        priority: data.priority || "normal",
        status: data.status || "pending",
        folder: located.folder,
        thread_id: data.metadata?.thread_id || "",
        msg_id: data.metadata?.msg_id || "",
        type: data.type || "email",
        metadata: data.metadata || {},
        tags: data.metadata?.tags || [],
        category: data.metadata?.category || "notification",
        requires_action: data.metadata?.requires_action || false,
        domain,
      },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch (error) {
    console.error("Error getting email:", error);
    return NextResponse.json({ error: "Failed to get email" }, { status: 500 });
  }
}

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { id } = await params;
    const { action, targetFolder, replyContent } = await request.json();

    const located = await findEmailById(id);
    if (!located) {
      return NextResponse.json({ success: false, error: "Email not found" }, { status: 404 });
    }

    const validFolders = ["Needs_Action", "Pending_Approval", "Approved", "Rejected", "Done"];

    if (action === "move") {
      if (!targetFolder || !validFolders.includes(targetFolder)) {
        return NextResponse.json({ success: false, error: "Invalid target folder" }, { status: 400 });
      }

      const targetPath = path.join(VAULT_PATH, targetFolder, located.relativeInFolder);
      await fs.mkdir(path.dirname(targetPath), { recursive: true });
      await fs.rename(located.filePath, targetPath);
      return NextResponse.json({ success: true, message: `Email moved to ${targetFolder}` });
    }

    if (action === "mark_read") {
      const parsed = matter(await fs.readFile(located.filePath, "utf-8"));
      parsed.data.status = "read";
      await fs.writeFile(located.filePath, matter.stringify(parsed.content, parsed.data), "utf-8");
      return NextResponse.json({ success: true, message: "Marked as read" });
    }

    if (action === "archive") {
      const archivePath = path.join(VAULT_PATH, "Done", located.relativeInFolder);
      await fs.mkdir(path.dirname(archivePath), { recursive: true });
      await fs.rename(located.filePath, archivePath);
      return NextResponse.json({ success: true, message: "Email archived" });
    }

    if (action === "create_reply") {
      const data = located.frontmatter;
      const domain = data.domain || resolveDomainFromRelative(located.relativeInFolder);
      const now = new Date().toISOString();
      const replyDraft = `---
id: "reply_${Date.now()}"
type: "email_reply"
action: "send_email"
domain: "${domain}"
parent_id: "${id}"
priority: "normal"
created: "${now}"
status: "pending"
metadata:
  to: "${data.metadata?.sender || data.from || ""}"
  subject: "Re: ${data.metadata?.subject || data.subject || ""}"
  in_reply_to: "${data.metadata?.msg_id || ""}"
  thread_id: "${data.metadata?.thread_id || ""}"
---

# Email Reply Draft

**To:** ${data.metadata?.sender || data.from || "Unknown"}
**Subject:** Re: ${data.metadata?.subject || data.subject || "No Subject"}

## Content

${replyContent || ""}

---

**[APPROVAL REQUIRED]** Move to /Approved to send, or /Rejected to discard.
`;

      const replyFilename = `REPLY_${id}_${Date.now()}.md`;
      const replyPath = path.join(VAULT_PATH, "Pending_Approval", domain, replyFilename);
      await fs.mkdir(path.dirname(replyPath), { recursive: true });
      await fs.writeFile(replyPath, replyDraft, "utf-8");

      return NextResponse.json({
        success: true,
        message: "Reply draft created in Pending_Approval",
        draftId: replyFilename.replace(".md", ""),
      });
    }

    return NextResponse.json({ success: false, error: "Unknown action" }, { status: 400 });
  } catch (error) {
    console.error("Error processing email action:", error);
    return NextResponse.json({ success: false, error: "Failed to process action" }, { status: 500 });
  }
}
