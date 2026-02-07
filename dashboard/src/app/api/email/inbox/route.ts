import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import matter from "gray-matter";

const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const VAULT_PATH = path.join(PROJECT_ROOT, "AI_Employee_Vault");

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const folder = searchParams.get('folder') || 'Needs_Action';

        const emails = [];
        const drafts = [];
        const folderCounts: Record<string, number> = {
            'Needs_Action': 0,
            'Pending_Approval': 0,
            'Approved': 0,
            'Done': 0,
            'Rejected': 0
        };

        // Determine which folders to read based on filter
        const foldersToRead = folder === 'all'
            ? ['Needs_Action', 'Pending_Approval', 'Approved', 'Done', 'Rejected']
            : [folder];

        // Read emails from selected folder(s)
        for (const currentFolder of foldersToRead) {
            const folderPath = path.join(VAULT_PATH, currentFolder);
            try {
                const files = await fs.readdir(folderPath);
                let emailCount = 0;

                for (const file of files) {
                    // Match both old "EMAIL_*.md" and new "*_gmail_watcher_email.md" or any email type
                    const isEmail = file.endsWith(".md") && (
                        file.startsWith("EMAIL") ||
                        file.startsWith("REPLY") ||
                        file.includes("gmail_watcher_email") ||
                        file.includes("_email")
                    );
                    if (!isEmail) continue;

                    try {
                        const filePath = path.join(folderPath, file);
                        const content = await fs.readFile(filePath, "utf-8");
                        const { data, content: body } = matter(content);

                        // Only include if type is email or email_reply
                        if (!['email', 'email_reply', 'email_draft'].includes(data.type || '')) continue;

                        emailCount++;

                        // Extract sender from metadata or frontmatter
                        const sender = data.metadata?.sender || data.metadata?.to || data.from || data.to || "Unknown";
                        const subject = data.metadata?.subject || data.subject || "No Subject";

                        emails.push({
                            id: data.id || file.replace(".md", ""),
                            from: sender,
                            subject: subject,
                            snippet: body.substring(0, 200).replace(/^#.*\n/gm, '').trim(),
                            time: data.timestamp || data.created || data.received || "",
                            read: data.status === "read" || data.status === "processed",
                            priority: data.priority || "normal",
                            tags: data.metadata?.tags || [],
                            category: data.metadata?.category || "notification",
                            requires_action: data.metadata?.requires_action || false,
                            folder: currentFolder,
                            isReply: data.type === "email_reply" || file.startsWith("REPLY")
                        });
                    } catch (error) {
                        console.error(`Error processing email ${file}:`, error);
                    }
                }

                folderCounts[currentFolder] = emailCount;
            } catch (error) {
                console.error(`Error reading ${currentFolder}:`, error);
            }
        }

        // Sort emails by timestamp (newest first)
        emails.sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime());

        // Read drafts from Pending_Approval and Approved
        const draftFolders = ["Pending_Approval", "Approved"];

        for (const folder of draftFolders) {
            const folderPath = path.join(VAULT_PATH, folder);

            try {
                const files = await fs.readdir(folderPath);

                for (const file of files) {
                    if ((!file.startsWith("EMAIL") && !file.startsWith("DRAFT")) || !file.endsWith(".md")) continue;

                    try {
                        const filePath = path.join(folderPath, file);
                        const content = await fs.readFile(filePath, "utf-8");
                        const { data } = matter(content);

                        if (data.action === "send_email" || data.type === "email_draft") {
                            drafts.push({
                                id: file.replace(".md", ""),
                                to: data.to || "Unknown",
                                subject: data.subject || "No Subject",
                                status: folder === "Pending_Approval" ? "pending" : folder === "Approved" ? "approved" : "sent",
                            });
                        }
                    } catch (error) {
                        console.error(`Error processing draft ${file}:`, error);
                    }
                }
            } catch (error) {
                console.error(`Error reading ${folder}:`, error);
            }
        }

        return NextResponse.json(
            { emails, drafts, folderCounts, _timestamp: Date.now() },
            {
                headers: {
                    'Cache-Control': 'no-store, no-cache, must-revalidate',
                    'Pragma': 'no-cache',
                }
            }
        );
    } catch (error) {
        console.error("Error getting email inbox:", error);
        return NextResponse.json({ emails: [], drafts: [] }, { status: 500 });
    }
}
