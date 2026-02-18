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
    const approvals = [];

    for (const filePath of files) {
      try {
        const content = await fs.readFile(filePath, "utf-8");
        const { data, content: body } = matter(content);
        const rel = normalizeVaultRelative(filePath); // Pending_Approval/.../*.md
        const relFromPending = rel.replace(/^Pending_Approval\//, "");
        const domain = relFromPending.includes("/") ? relFromPending.split("/")[0] : "general";

        approvals.push({
          id: encodeFileIdFromRelative(relFromPending),
          title: data.subject || data.title || relFromPending.replace(/\.md$/i, "").replace(/_/g, " "),
          type: data.type || "unknown",
          content: body.trim(),
          priority: data.priority || "normal",
          timestamp: data.created || data.timestamp || new Date().toISOString(),
          action: data.action || data.action_type || "",
          platform: data.platform || "",
          domain,
          path: rel,
        });
      } catch (error) {
        console.error(`Error processing approval file ${filePath}:`, error);
      }
    }

    return NextResponse.json(
      { approvals, _timestamp: Date.now() },
      {
        headers: {
          "Cache-Control": "no-store, no-cache, must-revalidate",
          Pragma: "no-cache",
        },
      },
    );
  } catch (error) {
    console.error("Error getting approvals:", error);
    return NextResponse.json({ approvals: [] }, { status: 500 });
  }
}
