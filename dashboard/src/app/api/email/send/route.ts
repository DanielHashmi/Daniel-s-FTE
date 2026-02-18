import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import matter from "gray-matter";
import { execFile } from "child_process";
import { promisify } from "util";
import {
  VAULT_PATH,
  encodeFileIdFromRelative,
  listMarkdownFilesRecursive,
} from "@/lib/vault";

const execFileAsync = promisify(execFile);
const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const PYTHON_EXE = process.env.PYTHON_EXE || "python";

export const dynamic = "force-dynamic";

function extractBody(markdownBody: string): string {
  const contentMatch = markdownBody.match(/## Content\s+([\s\S]*?)(?=\n\n---|$)/i);
  return contentMatch ? contentMatch[1].trim() : markdownBody.trim();
}

export async function POST(request: Request) {
  try {
    const { id } = await request.json();
    if (!id) {
      return NextResponse.json({ success: false, error: "Email ID required" }, { status: 400 });
    }

    const approvedFiles = await listMarkdownFilesRecursive("Approved");
    let selectedPath = "";
    let selectedData: any = null;
    let selectedBody = "";
    let selectedRel = "";

    for (const filePath of approvedFiles) {
      if (!filePath.toLowerCase().endsWith(".md")) continue;
      const raw = await fs.readFile(filePath, "utf-8");
      const parsed = matter(raw);
      const data = parsed.data || {};
      const rel = path.relative(path.join(VAULT_PATH, "Approved"), filePath).split(path.sep).join("/");
      const encodedId = encodeFileIdFromRelative(rel);

      if (String(data.id || "") === String(id) || encodedId === String(id)) {
        selectedPath = filePath;
        selectedData = data;
        selectedBody = parsed.content;
        selectedRel = rel;
        break;
      }
    }

    if (!selectedPath || !selectedData) {
      return NextResponse.json({ success: false, error: "Email not found in Approved folder" }, { status: 404 });
    }

    const to = String(selectedData.metadata?.to || selectedData.to || "").trim();
    const subject = String(selectedData.metadata?.subject || selectedData.subject || "").trim();
    const body = extractBody(selectedBody);

    if (!to || !subject || !body) {
      return NextResponse.json(
        { success: false, error: "Missing required email fields (to, subject, or body)" },
        { status: 400 },
      );
    }

    const skillPath = path.join(PROJECT_ROOT, ".claude", "skills", "email-ops", "scripts", "main_operation.py");
    const args = [skillPath, "--action", "send", "--to", to, "--subject", subject, "--body", body];

    try {
      const { stdout, stderr } = await execFileAsync(PYTHON_EXE, args, {
        cwd: PROJECT_ROOT,
        timeout: 60000,
        env: { ...process.env },
        maxBuffer: 1024 * 1024,
      });

      if (stderr?.trim()) {
        console.warn("email-ops stderr:", stderr.trim());
      }

      const donePath = path.join(VAULT_PATH, "Done", selectedRel);
      await fs.mkdir(path.dirname(donePath), { recursive: true });
      await fs.rename(selectedPath, donePath);

      return NextResponse.json({
        success: true,
        message: "Email sent successfully",
        details: String(stdout || "").trim(),
      });
    } catch (error: any) {
      console.error("Error sending email:", error);
      const stderr = String(error?.stderr || error?.message || "");
      return NextResponse.json({ success: false, error: stderr || "Failed to send email" }, { status: 500 });
    }
  } catch (error) {
    console.error("Error in send endpoint:", error);
    return NextResponse.json({ success: false, error: "Failed to process send request" }, { status: 500 });
  }
}
