import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import {
  VAULT_PATH,
  findMarkdownFileById,
  movePreserveDomain,
  normalizeVaultRelative,
} from "@/lib/vault";

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { action } = await request.json();
    const { id } = await params;

    if (!["approve", "reject"].includes(String(action || ""))) {
      return NextResponse.json({ success: false, error: "Invalid action" }, { status: 400 });
    }

    const pendingPath = await findMarkdownFileById("Pending_Approval", id);
    if (!pendingPath) {
      return NextResponse.json({ success: false, error: "File not found" }, { status: 404 });
    }

    const targetFolder = action === "approve" ? "Approved" : "Rejected";
    const targetPath = await movePreserveDomain(pendingPath, "Pending_Approval", targetFolder);

    // Create signal file for orchestrator (local merges cloud signals into dashboard).
    const signalsDir = path.join(VAULT_PATH, "Signals");
    await fs.mkdir(signalsDir, { recursive: true });
    const rel = normalizeVaultRelative(targetPath);
    const signalFile = path.join(signalsDir, `${Date.now()}_${action}.md`);
    await fs.writeFile(signalFile, `${action.toUpperCase()} ${rel}\n`, "utf-8");

    return NextResponse.json({
      success: true,
      message: `Approval ${action}d successfully`,
      path: rel,
    });
  } catch (error) {
    console.error("Error processing approval:", error);
    return NextResponse.json({ success: false, error: "Failed to process approval" }, { status: 500 });
  }
}
