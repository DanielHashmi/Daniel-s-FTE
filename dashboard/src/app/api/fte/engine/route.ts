import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";

const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const ENV_PATH = path.join(PROJECT_ROOT, ".env");

export async function POST(request: Request) {
    try {
        const { engine } = await request.json();

        if (!["claude", "qwen"].includes(engine)) {
            return NextResponse.json({
                success: false,
                error: "Invalid engine. Must be 'claude' or 'qwen'"
            }, { status: 400 });
        }

        const envContent = await fs.readFile(ENV_PATH, "utf-8");
        let lines = envContent.split("\n");
        let found = false;

        const newLines = lines.map(line => {
            if (line.trim().startsWith("REASONING_ENGINE=")) {
                found = true;
                return `REASONING_ENGINE=${engine}`;
            }
            return line;
        });

        if (!found) {
            newLines.push(`REASONING_ENGINE=${engine}`);
        }

        await fs.writeFile(ENV_PATH, newLines.join("\n"));

        // We also need to restart the orchestrator for this to take effect if it reads env only on startup. 
        // But PlanManager reads os.environ. Since os.environ isn't updated by file change, 
        // we might need to restart.
        // However, we can probably rely on the Restart FTE button or build auto-restart into this.
        // For "fully working autonomous" experience, let's restart if running.

        // Actually, Restarting logic is complex. The user can hit Restart manually.
        // But "PlanManager" in the python process reads "os.environ.get" which is process-level.
        // Changing .env won't change the running python process's environment.
        // So we MUST restart the orchestrator.

        return NextResponse.json({
            success: true,
            message: `Engine switched to ${engine}. Please restart FTE to apply.`
        });

    } catch (error) {
        console.error("Error switching engine:", error);
        return NextResponse.json({
            success: false,
            error: "Failed to switch engine"
        }, { status: 500 });
    }
}

export const dynamic = 'force-dynamic';

export async function GET() {
    try {
        const envContent = await fs.readFile(ENV_PATH, "utf-8");
        const lines = envContent.split("\n");
        let engine = "qwen"; // default
        let mode = "dry_run";

        for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith("REASONING_ENGINE=")) {
                engine = trimmed.split("=")[1].trim().toLowerCase();
            }
            if (trimmed.startsWith("DRY_RUN=")) {
                mode = trimmed.split("=")[1].trim() === "true" ? "dry_run" : "live";
            }
        }

        return NextResponse.json({ engine, mode });
    } catch (error) {
        return NextResponse.json({ engine: "qwen", mode: "dry_run" });
    }
}
