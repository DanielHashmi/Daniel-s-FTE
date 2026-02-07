import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import matter from "gray-matter";

const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const VAULT_PATH = path.join(PROJECT_ROOT, "AI_Employee_Vault");

export const dynamic = 'force-dynamic';

// GET single email
export async function GET(
    request: Request,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;

        // Search in all possible folders
        const folders = ["Needs_Action", "Pending_Approval", "Approved", "Rejected", "Done"];

        for (const folder of folders) {
            const folderPath = path.join(VAULT_PATH, folder);

            try {
                const files = await fs.readdir(folderPath);

                // Search through files to find one with matching ID
                for (const file of files) {
                    if (!file.endsWith(".md")) continue;

                    const filePath = path.join(folderPath, file);
                    const content = await fs.readFile(filePath, "utf-8");
                    const { data, content: body } = matter(content);

                    // Check if this file's ID matches
                    if (data.id === id) {
                        return NextResponse.json({
                            id: data.id,
                            filename: file,
                            from: data.metadata?.sender || data.from || "Unknown",
                            subject: data.metadata?.subject || data.subject || "No Subject",
                            body: body.trim(),
                            timestamp: data.timestamp || "",
                            priority: data.priority || "normal",
                            status: data.status || "pending",
                            folder: folder,
                            thread_id: data.metadata?.thread_id || "",
                            msg_id: data.metadata?.msg_id || "",
                            type: data.type || "email",
                            metadata: data.metadata || {},
                            tags: data.metadata?.tags || [],
                            category: data.metadata?.category || "notification",
                            requires_action: data.metadata?.requires_action || false,
                        }, {
                            headers: {
                                'Cache-Control': 'no-store',
                            }
                        });
                    }
                }
            } catch (error) {
                // Folder might not exist, continue
                continue;
            }
        }

        return NextResponse.json({
            error: "Email not found"
        }, { status: 404 });

    } catch (error) {
        console.error("Error getting email:", error);
        return NextResponse.json({
            error: "Failed to get email"
        }, { status: 500 });
    }
}

// POST - Move email to different folder or perform action
export async function POST(
    request: Request,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const { action, targetFolder, replyContent } = await request.json();

        // Find current location by searching for ID in frontmatter
        const folders = ["Needs_Action", "Pending_Approval", "Approved", "Rejected", "Done"];
        let currentFolder = "";
        let currentPath = "";
        let currentFilename = "";

        for (const folder of folders) {
            const folderPath = path.join(VAULT_PATH, folder);

            try {
                const files = await fs.readdir(folderPath);

                for (const file of files) {
                    if (!file.endsWith(".md")) continue;

                    const filePath = path.join(folderPath, file);
                    const content = await fs.readFile(filePath, "utf-8");
                    const { data } = matter(content);

                    if (data.id === id) {
                        currentFolder = folder;
                        currentPath = filePath;
                        currentFilename = file;
                        break;
                    }
                }

                if (currentPath) break;
            } catch {
                continue;
            }
        }

        if (!currentPath) {
            return NextResponse.json({
                success: false,
                error: "Email not found"
            }, { status: 404 });
        }

        // Handle different actions
        switch (action) {
            case "move":
                if (!targetFolder || !folders.includes(targetFolder)) {
                    return NextResponse.json({
                        success: false,
                        error: "Invalid target folder"
                    }, { status: 400 });
                }

                const targetPath = path.join(VAULT_PATH, targetFolder, currentFilename);
                await fs.rename(currentPath, targetPath);

                return NextResponse.json({
                    success: true,
                    message: `Email moved to ${targetFolder}`
                });

            case "mark_read":
                const content = await fs.readFile(currentPath, "utf-8");
                const parsed = matter(content);
                parsed.data.status = "read";
                const newContent = matter.stringify(parsed.content, parsed.data);
                await fs.writeFile(currentPath, newContent);

                return NextResponse.json({
                    success: true,
                    message: "Marked as read"
                });

            case "archive":
                const archivePath = path.join(VAULT_PATH, "Done", currentFilename);
                await fs.rename(currentPath, archivePath);

                return NextResponse.json({
                    success: true,
                    message: "Email archived"
                });

            case "create_reply":
                // Create a draft reply in Pending_Approval
                const originalContent = await fs.readFile(currentPath, "utf-8");
                const { data: originalData } = matter(originalContent);

                const replyDraft = `---
id: "reply_${Date.now()}"
type: "email_reply"
action: "send_email"
parent_id: "${id}"
priority: "normal"
created: "${new Date().toISOString()}"
status: "pending"
metadata:
  to: "${originalData.metadata?.sender || originalData.from}"
  subject: "Re: ${originalData.metadata?.subject || originalData.subject}"
  in_reply_to: "${originalData.metadata?.msg_id}"
  thread_id: "${originalData.metadata?.thread_id}"
---

# Email Reply Draft

**To:** ${originalData.metadata?.sender || originalData.from}
**Subject:** Re: ${originalData.metadata?.subject || originalData.subject}

## Content

${replyContent || ""}

---

**[APPROVAL REQUIRED]** This email will be sent after approval.

Move to /Approved/ to send, or /Rejected/ to discard.
`;

                const replyFilename = `REPLY_${id}_${Date.now()}.md`;
                const replyPath = path.join(VAULT_PATH, "Pending_Approval", replyFilename);
                await fs.writeFile(replyPath, replyDraft);

                return NextResponse.json({
                    success: true,
                    message: "Reply draft created in Pending_Approval",
                    draftId: replyFilename.replace(".md", "")
                });

            default:
                return NextResponse.json({
                    success: false,
                    error: "Unknown action"
                }, { status: 400 });
        }

    } catch (error) {
        console.error("Error processing email action:", error);
        return NextResponse.json({
            success: false,
            error: "Failed to process action"
        }, { status: 500 });
    }
}
