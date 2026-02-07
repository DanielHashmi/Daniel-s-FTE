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
        // First, update status file to signal stop
        const statusFile = path.join(VAULT_PATH, ".fte_status");
        await fs.writeFile(statusFile, "stopped");

        // Kill Python orchestrator processes
        try {
            // Get all python processes and filter for orchestrator
            const { stdout } = await execAsync('wmic process where "name=\'python.exe\'" get commandline,processid /format:csv');
            const lines = stdout.split('\n');

            const pidsToKill: string[] = [];
            for (const line of lines) {
                if (line.includes('orchestrator.py') || line.includes('gmail') || line.includes('linkedin') || line.includes('whatsapp') || line.includes('odoo')) {
                    const parts = line.split(',');
                    const pid = parts[parts.length - 1]?.trim();
                    if (pid && !isNaN(parseInt(pid))) {
                        pidsToKill.push(pid);
                    }
                }
            }

            // Kill each process by PID
            for (const pid of pidsToKill) {
                try {
                    await execAsync(`taskkill /F /PID ${pid}`);
                } catch (e) {
                    // Process might have already stopped
                }
            }

        } catch (error) {
            console.log("Error stopping processes:", error);
            // Fallback: try to kill all python.exe (more aggressive)
            try {
                await execAsync('taskkill /F /IM python.exe');
            } catch (e) {
                // No python processes running
            }
        }

        return NextResponse.json({
            success: true,
            message: "FTE stopped successfully"
        });
    } catch (error) {
        console.error("Error stopping FTE:", error);
        return NextResponse.json({
            success: false,
            error: "Failed to stop FTE"
        }, { status: 500 });
    }
}
