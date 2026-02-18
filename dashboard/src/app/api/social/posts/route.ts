import { NextResponse } from "next/server";
import fs from "fs/promises";
import matter from "gray-matter";
import {
  encodeFileIdFromRelative,
  listMarkdownFilesRecursive,
  normalizeVaultRelative,
} from "@/lib/vault";

export const dynamic = "force-dynamic";

type SocialPostRow = {
  id: string;
  platform: string;
  content: string;
  status: "pending" | "approved" | "posted" | "failed";
  createdAt: string;
  brain: string;
  domain: string;
  sourceFolder: string;
  path: string;
};

export async function GET() {
  try {
    const posts: SocialPostRow[] = [];
    const seenByPath = new Set<string>();
    const folders = ["Pending_Approval", "Approved", "Done", "Recovery_Queue"];

    for (const folder of folders) {
      const files = await listMarkdownFilesRecursive(folder);
      for (const filePath of files) {
        const fileName = filePath.split(/[/\\]/).pop() || "";
        if (!fileName.endsWith(".md")) continue;

        try {
          const content = await fs.readFile(filePath, "utf-8");
          const { data, content: body } = matter(content);

          const action = String(data.action || data.action_type || "").toLowerCase();
          const type = String(data.type || "").toLowerCase();
          const isSocial =
            action === "social_post" ||
            type === "social" ||
            fileName.startsWith("SOCIAL") ||
            fileName.toLowerCase().includes("social");
          if (!isSocial) continue;

          const contentMatch = body.match(/## Content\s*([\s\S]*?)(\n## |\n\*|$)/i);
          const postContent = contentMatch ? contentMatch[1].trim() : body.trim().substring(0, 280);

          const rel = normalizeVaultRelative(filePath);
          if (seenByPath.has(rel)) continue;
          seenByPath.add(rel);

          const relInFolder = rel.replace(new RegExp(`^${folder}/`), "");
          const domain = relInFolder.includes("/") ? relInFolder.split("/")[0] : "general";

          posts.push({
            id: encodeFileIdFromRelative(`${folder}/${relInFolder}`),
            platform: data.platform || "twitter",
            content: postContent,
            status:
              folder === "Pending_Approval"
                ? "pending"
                : folder === "Approved"
                  ? "approved"
                  : folder === "Recovery_Queue"
                    ? "failed"
                    : "posted",
            createdAt: data.created || data.timestamp || "",
            brain: data.brain || "manual",
            domain,
            sourceFolder: folder,
            path: rel,
          });
        } catch (error) {
          console.error(`Error processing social file ${filePath}:`, error);
        }
      }
    }

    posts.sort((a, b) => {
      const ta = Date.parse(String(a.createdAt || "")) || 0;
      const tb = Date.parse(String(b.createdAt || "")) || 0;
      if (tb !== ta) return tb - ta;
      return String(b.path || "").localeCompare(String(a.path || ""));
    });

    return NextResponse.json(
      { posts, _timestamp: Date.now() },
      {
        headers: {
          "Cache-Control": "no-store, no-cache, must-revalidate",
          Pragma: "no-cache",
        },
      },
    );
  } catch (error) {
    console.error("Error getting social posts:", error);
    return NextResponse.json({ posts: [] }, { status: 500 });
  }
}
