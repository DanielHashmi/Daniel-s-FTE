import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import fs from "fs/promises";
import path from "path";

const execAsync = promisify(exec);

const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const VAULT_PATH = path.join(PROJECT_ROOT, "AI_Employee_Vault");

export async function POST() {
    try {
        // Use START_BRAIN.bat which properly launches the orchestrator with all watchers
        const startScript = path.join(PROJECT_ROOT, "START_BRAIN.bat");

        try {
            // Check if script exists
            await fs.access(startScript);

            // Execute start script in background
            exec(`cmd /c start "" "${startScript}"`, { cwd: PROJECT_ROOT }, (error) => {
                if (error) console.error("Error executing start script:", error);
            });

            // Update status file
            const statusFile = path.join(VAULT_PATH, ".fte_status");
            await fs.writeFile(statusFile, "running");

            // Give it a moment to start
            await new Promise(resolve => setTimeout(resolve, 2000));

            return NextResponse.json({
                success: true,
                message: "FTE started successfully"
            });
        } catch (error) {
            // Fallback: Start orchestrator directly
            const orchestratorCmd = `python -m src.orchestration.orchestrator`;
            exec(orchestratorCmd, { cwd: PROJECT_ROOT }, (error) => {
                if (error) console.error("Error starting orchestrator:", error);
            });

            const statusFile = path.join(VAULT_PATH, ".fte_status");
            await fs.writeFile(statusFile, "running");

            return NextResponse.json({
                success: true,
                message: "FTE started (fallback mode)"
            });
        }
    } catch (error) {
        console.error("Error starting FTE:", error);
        return NextResponse.json({
            success: false,
            error: "Failed to start FTE"
        }, { status: 500 });
    }
}
