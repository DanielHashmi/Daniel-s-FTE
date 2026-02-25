import { NextResponse } from "next/server";
import fs from "fs/promises";
import matter from "gray-matter";
import {
  encodeFileIdFromRelative,
  listMarkdownFilesRecursive,
  normalizeVaultRelative,
} from "@/lib/vault";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const files = await listMarkdownFilesRecursive("Pending_Approval");
    const posts = [];

    for (const filePath of files) {
      const fileName = filePath.split(/[/\\]/).pop() || "";
      if (!fileName.endsWith(".md")) continue;

      const content = await fs.readFile(filePath, "utf-8").catch(() => "");
      if (!content) continue;

      const parsed = matter(content);
      const data = parsed.data as Record<string, any>;
      const body = parsed.content || "";
      const action = String(data.action || data.action_type || "").toLowerCase();
      const type = String(data.type || "").toLowerCase();
      const isSocial =
        action === "social_post" ||
        type === "social" ||
        fileName.toLowerCase().includes("social") ||
        fileName.toLowerCase().includes("post");
      if (!isSocial) continue;

      const rel = normalizeVaultRelative(filePath);
      const relFromPending = rel.replace(/^Pending_Approval\//, "");
      const domain = relFromPending.includes("/") ? relFromPending.split("/")[0] : "general";

      const platforms: string[] = [];
      const platform = String(data.platform || "").toLowerCase();
      if (platform) platforms.push(platform);
      if (platforms.length === 0) {
        const txt = `${body}\n${JSON.stringify(data)}`.toLowerCase();
        if (txt.includes("twitter")) platforms.push("twitter");
        if (txt.includes("facebook")) platforms.push("facebook");
        if (txt.includes("instagram")) platforms.push("instagram");
        if (txt.includes("linkedin")) platforms.push("linkedin");
      }

      posts.push({
        id: encodeFileIdFromRelative(relFromPending),
        platforms: platforms.length > 0 ? platforms : ["twitter"],
        content: body.trim().substring(0, 500),
        status: "pending",
        createdAt: String(data.created || data.timestamp || "Unknown"),
        domain,
        path: rel,
      });
    }

    return NextResponse.json({ posts });
  } catch (error) {
    console.error("Failed to get pending posts:", error);
    return NextResponse.json({ posts: [] }, { status: 500 });
  }
}
