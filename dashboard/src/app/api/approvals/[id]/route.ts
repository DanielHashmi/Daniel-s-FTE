import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";

const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const VAULT_PATH = path.join(PROJECT_ROOT, "AI_Employee_Vault");

export async function POST(
    request: Request,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { action } = await request.json();
        const { id } = await params;
        const filename = `${id}.md`;

        const pendingPath = path.join(VAULT_PATH, "Pending_Approval", filename);
        const targetFolder = action === "approve" ? "Approved" : "Rejected";
        const targetPath = path.join(VAULT_PATH, targetFolder, filename);

        // Check if file exists
        try {
            await fs.access(pendingPath);
        } catch (error) {
            return NextResponse.json({
                success: false,
                error: "File not found"
            }, { status: 404 });
        }

        // Move file
        await fs.rename(pendingPath, targetPath);

        // Create signal file for orchestrator
        const signalPath = path.join(VAULT_PATH, "Signals", `${action}_${id}.signal`);
        await fs.writeFile(signalPath, new Date().toISOString());

        return NextResponse.json({
            success: true,
            message: `Approval ${action}d successfully`
        });
    } catch (error) {
        console.error("Error processing approval:", error);
        return NextResponse.json({
            success: false,
            error: "Failed to process approval"
        }, { status: 500 });
    }
}
