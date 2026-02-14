import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import { buildFacebookQwenPrompt, runQwenPrompt } from "@/lib/qwen";

const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const VAULT_PATH = path.join(PROJECT_ROOT, "AI_Employee_Vault");

function indentBlock(text: string, spaces = 2): string {
    const indent = " ".repeat(spaces);
    return text
        .split(/\r?\n/)
        .map((line) => `${indent}${line}`)
        .join("\n");
}

export async function POST(request: Request) {
    try {
        const { content, platforms, qwenPrompt } = await request.json();

        if (!Array.isArray(platforms) || platforms.length === 0) {
            return NextResponse.json({
                success: false,
                error: "At least one platform is required"
            }, { status: 400 });
        }

        const rawContent = String(content || "").trim();
        const rawQwenPrompt = String(qwenPrompt || "").trim();
        if (!rawContent && !rawQwenPrompt) {
            return NextResponse.json(
                { success: false, error: "content or qwenPrompt is required" },
                { status: 400 }
            );
        }
        const nowIso = new Date().toISOString();
        const timestamp = nowIso.replace(/[:.]/g, "-");
        const createdIds: string[] = [];
        let generatedFacebookContent = "";

        for (let i = 0; i < platforms.length; i++) {
            const platform = String(platforms[i] || "").trim().toLowerCase();
            if (!platform) continue;

            let finalContent = rawContent;
            let brain = "manual";
            let promptUsed = "";

            if (platform === "facebook") {
                brain = "qwen";
                promptUsed = rawQwenPrompt || rawContent;
                if (!promptUsed) {
                    return NextResponse.json(
                        {
                            success: false,
                            error: "Facebook posting requires a qwenPrompt or seed content",
                        },
                        { status: 400 }
                    );
                }

                // If the user already provided content (often generated via the UI "Generate with Qwen"
                // button and optionally edited), do NOT regenerate here. The human must be approving
                // exactly what is written to Pending_Approval.
                if (!finalContent.trim()) {
                    const qwenPromptText = buildFacebookQwenPrompt(promptUsed, rawContent);
                    finalContent = await runQwenPrompt(qwenPromptText);
                    generatedFacebookContent = finalContent;
                }
            } else if (!finalContent && generatedFacebookContent) {
                finalContent = generatedFacebookContent;
            }

            if (!finalContent.trim()) {
                return NextResponse.json(
                    { success: false, error: `Empty content for platform: ${platform}` },
                    { status: 400 }
                );
            }

            const filename = `SOCIAL_${platform.toUpperCase()}_${timestamp}_${i + 1}.md`;
            const id = filename.replace(".md", "");
            const safeContent = finalContent.replace(/\r/g, "");

            const frontmatter = `---
type: social
action: social_post
platform: ${platform}
status: pending
created: ${nowIso}
priority: normal
requires_approval: true
brain: ${brain}
${promptUsed ? `qwen_prompt: |\n${indentBlock(promptUsed, 2)}` : ""}
---

## Content
${safeContent}

*This post requires approval before posting*
`;

            const filePath = path.join(VAULT_PATH, "Pending_Approval", filename);
            await fs.writeFile(filePath, frontmatter, "utf-8");
            createdIds.push(id);
        }

        return NextResponse.json({
            success: true,
            message: "Post created and pending approval",
            ids: createdIds,
        });
    } catch (error) {
        console.error("Error creating social post:", error);
        return NextResponse.json({
            success: false,
            error: error instanceof Error ? error.message : "Failed to create post"
        }, { status: 500 });
    }
}
