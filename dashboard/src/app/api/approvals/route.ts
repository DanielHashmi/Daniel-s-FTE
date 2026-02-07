import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import matter from "gray-matter";

const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const VAULT_PATH = path.join(PROJECT_ROOT, "AI_Employee_Vault");

export const dynamic = 'force-dynamic';

export async function GET() {
    try {
        const pendingPath = path.join(VAULT_PATH, "Pending_Approval");

        let files: string[] = [];
        try {
            files = await fs.readdir(pendingPath);
        } catch (error) {
            console.error("Error reading Pending_Approval folder:", error);
            return NextResponse.json({ approvals: [] });
        }

        const approvals = [];

        for (const file of files) {
            if (!file.endsWith(".md")) continue;

            try {
                const filePath = path.join(pendingPath, file);
                const content = await fs.readFile(filePath, "utf-8");
                const { data, content: body } = matter(content);

                approvals.push({
                    id: file.replace(".md", ""),
                    title: data.subject || data.title || file.replace(".md", "").replace(/_/g, " "),
                    type: data.type || "unknown",
                    content: body.trim(),
                    priority: data.priority || "normal",
                    timestamp: data.created || data.timestamp || new Date().toISOString(),
                    action: data.action || "",
                    platform: data.platform || "",
                });
            } catch (error) {
                console.error(`Error processing file ${file}:`, error);
            }
        }

        return NextResponse.json(
            { approvals, _timestamp: Date.now() },
            {
                headers: {
                    'Cache-Control': 'no-store, no-cache, must-revalidate',
                    'Pragma': 'no-cache',
                }
            }
        );
    } catch (error) {
        console.error("Error getting approvals:", error);
        return NextResponse.json({ approvals: [] }, { status: 500 });
    }
}
