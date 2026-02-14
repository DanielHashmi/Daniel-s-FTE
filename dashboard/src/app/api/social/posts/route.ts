import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import matter from "gray-matter";

const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const VAULT_PATH = path.join(PROJECT_ROOT, "AI_Employee_Vault");

export const dynamic = 'force-dynamic';

export async function GET() {
    try {
        const posts = [];
        const folders = ["Pending_Approval", "Approved", "Done"];

        for (const folder of folders) {
            const folderPath = path.join(VAULT_PATH, folder);

            try {
                const files = await fs.readdir(folderPath);

                for (const file of files) {
                    if (!file.startsWith("SOCIAL") && !file.includes("social")) continue;
                    if (!file.endsWith(".md")) continue;

                    try {
                        const filePath = path.join(folderPath, file);
                        const content = await fs.readFile(filePath, "utf-8");
                        const { data, content: body } = matter(content);

                        if (data.type === "social" || file.includes("SOCIAL")) {
                            // Extract content
                            const contentMatch = body.match(/## Content[\s\S]*?^(.+?)(?=\n\n|\*This post|$)/m);
                            const postContent = contentMatch ? contentMatch[1].trim() : body.trim().substring(0, 280);

                            posts.push({
                                id: file.replace(".md", ""),
                                platform: data.platform || data.platforms?.split(",")[0]?.trim() || "twitter",
                                content: postContent,
                                status: folder === "Pending_Approval" ? "pending" : folder === "Approved" ? "approved" : "posted",
                                createdAt: data.created || data.timestamp || "",
                                brain: data.brain || "manual",
                            });
                        }
                    } catch (error) {
                        console.error(`Error processing file ${file}:`, error);
                    }
                }
            } catch (error) {
                console.error(`Error reading folder ${folder}:`, error);
            }
        }

        return NextResponse.json(
            { posts, _timestamp: Date.now() },
            {
                headers: {
                    'Cache-Control': 'no-store, no-cache, must-revalidate',
                    'Pragma': 'no-cache',
                }
            }
        );
    } catch (error) {
        console.error("Error getting social posts:", error);
        return NextResponse.json({ posts: [] }, { status: 500 });
    }
}
