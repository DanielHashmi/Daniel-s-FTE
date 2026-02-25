import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import {
  buildFacebookQwenPrompt,
  buildInstagramQwenPrompt,
  normalizeQwenOutput,
  runQwenPrompt,
} from "@/lib/qwen";
import { VAULT_PATH } from "@/lib/vault";

function indentBlock(text: string, spaces = 2): string {
  const indent = " ".repeat(spaces);
  return text
    .split(/\r?\n/)
    .map((line) => `${indent}${line}`)
    .join("\n");
}

function isValidHttpUrl(value: string): boolean {
  return /^https?:\/\/\S+$/i.test(value.trim());
}

function isValidE164(value: string): boolean {
  return /^\+?[1-9]\d{6,14}$/.test(value.trim());
}

function parseHashtags(raw: string): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  for (const token of raw.split(/[,\s]+/g).map((s) => s.trim()).filter(Boolean)) {
    const normalized = token.startsWith("#") ? token : `#${token}`;
    const safe = normalized.replace(/[^\w#]/g, "");
    if (!safe || safe === "#") continue;
    const key = safe.toLowerCase();
    if (!seen.has(key)) {
      seen.add(key);
      out.push(safe);
    }
  }
  return out.slice(0, 12);
}

function extractHashtagsFromText(text: string): string[] {
  const matches = text.match(/#[A-Za-z0-9_]+/g) || [];
  const out: string[] = [];
  const seen = new Set<string>();
  for (const tag of matches) {
    const key = tag.toLowerCase();
    if (!seen.has(key)) {
      seen.add(key);
      out.push(tag);
    }
  }
  return out;
}

function appendMissingHashtags(caption: string, tags: string[]): string {
  if (!tags.length) return caption.trim();
  const existing = new Set(extractHashtagsFromText(caption).map((t) => t.toLowerCase()));
  const missing = tags.filter((t) => !existing.has(t.toLowerCase()));
  if (!missing.length) return caption.trim();
  return `${caption.trim()}\n\n${missing.join(" ")}`.trim();
}

function yamlSafeQuote(value: string): string {
  return `"${value.replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
}

export async function POST(request: Request) {
  try {
    const {
      content,
      platforms,
      qwenPrompt,
      domain = "business",
      autoApprove = false,
      instagramImageUrl,
      instagramHashtags,
      whatsappTo,
    } = await request.json();

    if (!Array.isArray(platforms) || platforms.length === 0) {
      return NextResponse.json({ success: false, error: "At least one platform is required" }, { status: 400 });
    }

    const normalizedPlatforms = platforms.map((p: unknown) => String(p || "").trim().toLowerCase()).filter(Boolean);
    if (normalizedPlatforms.length === 0) {
      return NextResponse.json({ success: false, error: "At least one valid platform is required" }, { status: 400 });
    }
    const supportedPlatforms = new Set(["facebook", "twitter", "linkedin", "instagram", "whatsapp"]);
    const unsupported = normalizedPlatforms.filter((p) => !supportedPlatforms.has(p));
    if (unsupported.length > 0) {
      return NextResponse.json(
        { success: false, error: `Unsupported platform(s): ${unsupported.join(", ")}` },
        { status: 400 },
      );
    }

    const rawContent = String(content || "").trim();
    const rawQwenPrompt = String(qwenPrompt || "").trim();
    if (!rawContent && !rawQwenPrompt) {
      return NextResponse.json({ success: false, error: "content or qwenPrompt is required" }, { status: 400 });
    }

    const needsInstagramPayload = normalizedPlatforms.includes("instagram");
    const needsWhatsAppPayload = normalizedPlatforms.includes("whatsapp");
    const rawInstagramImageUrl = String(instagramImageUrl || "").trim();
    const explicitInstagramTags = parseHashtags(String(instagramHashtags || "").trim());
    const rawWhatsAppTo = String(whatsappTo || "").trim();

    if (needsInstagramPayload) {
      if (!rawInstagramImageUrl) {
        return NextResponse.json({ success: false, error: "Instagram requires image URL" }, { status: 400 });
      }
      if (!isValidHttpUrl(rawInstagramImageUrl)) {
        return NextResponse.json(
          { success: false, error: "Instagram image URL must be a valid http/https URL" },
          { status: 400 },
        );
      }
    }

    if (needsWhatsAppPayload) {
      if (!rawWhatsAppTo) {
        return NextResponse.json(
          { success: false, error: "WhatsApp requires recipient number (E.164 format)" },
          { status: 400 },
        );
      }
      if (!isValidE164(rawWhatsAppTo)) {
        return NextResponse.json(
          { success: false, error: "WhatsApp recipient must be a valid E.164 number (e.g. +15551234567)" },
          { status: 400 },
        );
      }
    }

    const nowIso = new Date().toISOString();
    const timestamp = nowIso.replace(/[:.]/g, "-");
    const normalizedDomain = String(domain || "business").toLowerCase();
    const createdIds: string[] = [];

    let generatedFacebookContent = "";
    let generatedInstagramCaption = "";

    for (let i = 0; i < normalizedPlatforms.length; i++) {
      const platform = normalizedPlatforms[i];

      let finalContent = rawContent;
      let brain = "manual";
      let promptUsed = "";
      const extraFrontmatter: string[] = [];
      const extraSections: string[] = [];

      if (platform === "facebook") {
        brain = "qwen";
        promptUsed = rawQwenPrompt || rawContent;
        if (!promptUsed) {
          return NextResponse.json(
            { success: false, error: "Facebook posting requires a qwenPrompt or seed content" },
            { status: 400 },
          );
        }

        if (!finalContent.trim()) {
          const qwenPromptText = buildFacebookQwenPrompt(promptUsed, rawContent);
          finalContent = await runQwenPrompt(qwenPromptText);
          generatedFacebookContent = finalContent;
        }
      } else if (platform === "instagram") {
        promptUsed = rawQwenPrompt;
        if (!finalContent.trim()) {
          const generationPrompt = rawQwenPrompt || rawContent;
          if (!generationPrompt) {
            return NextResponse.json(
              { success: false, error: "Instagram posting requires a qwenPrompt or caption content" },
              { status: 400 },
            );
          }
          brain = "qwen";
          promptUsed = generationPrompt;
          const qwenPromptText = buildInstagramQwenPrompt(generationPrompt, rawContent);
          finalContent = await runQwenPrompt(qwenPromptText);
          generatedInstagramCaption = finalContent;
        } else if (promptUsed) {
          brain = "qwen";
        }
      } else if (!finalContent && generatedFacebookContent) {
        finalContent = generatedFacebookContent;
      } else if (!finalContent && generatedInstagramCaption) {
        finalContent = generatedInstagramCaption;
      }

      if (!finalContent.trim()) {
        return NextResponse.json({ success: false, error: `Empty content for platform: ${platform}` }, { status: 400 });
      }

      finalContent = normalizeQwenOutput(finalContent);
      if (!finalContent.trim()) {
        return NextResponse.json(
          { success: false, error: `Invalid generated content for platform: ${platform}` },
          { status: 400 },
        );
      }
      if (platform === "whatsapp" && finalContent.length > 4096) {
        finalContent = `${finalContent.slice(0, 4093).trimEnd()}...`;
      }

      if (platform === "instagram") {
        finalContent = appendMissingHashtags(finalContent, explicitInstagramTags);
        const inferredTags = explicitInstagramTags.length > 0 ? explicitInstagramTags : extractHashtagsFromText(finalContent);

        extraFrontmatter.push(`image_url: ${yamlSafeQuote(rawInstagramImageUrl)}`);
        extraFrontmatter.push(`caption: |\n${indentBlock(finalContent, 2)}`);
        if (explicitInstagramTags.length > 0) {
          extraFrontmatter.push(`hashtags: ${yamlSafeQuote(explicitInstagramTags.join(","))}`);
        }

        extraSections.push(`## Image URL\n${rawInstagramImageUrl}`);
        if (inferredTags.length > 0) {
          extraSections.push(`## Hashtags\n${inferredTags.join(" ")}`);
        }
      } else if (platform === "whatsapp") {
        extraFrontmatter.push(`to: ${yamlSafeQuote(rawWhatsAppTo)}`);
        extraFrontmatter.push(`whatsapp_to: ${yamlSafeQuote(rawWhatsAppTo)}`);
        extraSections.push(`## Recipient\n${rawWhatsAppTo}`);
      }

      const filename = `SOCIAL_${platform.toUpperCase()}_${timestamp}_${i + 1}.md`;
      const id = filename.replace(".md", "");
      const safeContent = finalContent.replace(/\r/g, "");

      const frontmatterLines = [
        "type: social",
        "action: social_post",
        `platform: ${platform}`,
        `domain: ${normalizedDomain}`,
        `auto_approve: ${autoApprove ? "true" : "false"}`,
        "status: pending",
        `created: ${nowIso}`,
        "priority: normal",
        "requires_approval: true",
        `brain: ${brain}`,
        ...(promptUsed ? [`qwen_prompt: |\n${indentBlock(promptUsed, 2)}`] : []),
        ...extraFrontmatter,
      ];

      const bodySections = [`## Content\n${safeContent}`, ...extraSections];
      const approvalDoc = `---
${frontmatterLines.join("\n")}
---

${bodySections.join("\n\n")}

*This post requires approval before posting*
`;

      const targetDir = path.join(VAULT_PATH, "Pending_Approval", normalizedDomain);
      await fs.mkdir(targetDir, { recursive: true });
      const filePath = path.join(targetDir, filename);
      await fs.writeFile(filePath, approvalDoc, "utf-8");
      createdIds.push(id);
    }

    return NextResponse.json({ success: true, message: "Post created and pending approval", ids: createdIds });
  } catch (error) {
    console.error("Error creating social post:", error);
    return NextResponse.json({ success: false, error: error instanceof Error ? error.message : "Failed to create post" }, { status: 500 });
  }
}
