import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";

const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const VAULT_PATH = path.join(PROJECT_ROOT, "AI_Employee_Vault");

export async function POST(request: Request) {
    try {
        const { content, platforms } = await request.json();

        if (!content || !platforms || platforms.length === 0) {
            return NextResponse.json({
                success: false,
                error: "Content and platforms are required"
            }, { status: 400 });
        }

        const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
        const filename = `SOCIAL_POST_${timestamp}.md`;

        const frontmatter = `---
type: social
action: post
platforms: ${platforms.join(", ")}
status: pending
created: ${new Date().toISOString()}
priority: normal
---

## Content
${content}

*This post requires approval before posting*
`;

        const filePath = path.join(VAULT_PATH, "Pending_Approval", filename);
        await fs.writeFile(filePath, frontmatter);

        return NextResponse.json({
            success: true,
            message: "Post created and pending approval",
            id: filename.replace(".md", "")
        });
    } catch (error) {
        console.error("Error creating social post:", error);
        return NextResponse.json({
            success: false,
            error: "Failed to create post"
        }, { status: 500 });
    }
}
