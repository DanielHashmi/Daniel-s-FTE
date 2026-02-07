import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import fs from "fs/promises";
import path from "path";

const execAsync = promisify(exec);

const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const VAULT_PATH = path.join(PROJECT_ROOT, "AI_Employee_Vault");

export const dynamic = 'force-dynamic';

export async function GET() {
    try {
        // Check if .fte_status file exists
        const statusFile = path.join(VAULT_PATH, ".fte_status");
        let running = false;

        try {
            const status = await fs.readFile(statusFile, "utf-8");
            running = status.trim() === "running";
        } catch (error) {
            // File doesn't exist, FTE is not running
            running = false;
        }

        // Get running Python processes
        const services: any[] = [];

        try {
            const { stdout } = await execAsync(`tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH`);
            const processes = stdout.split("\n").filter((line: string) => line.includes("python.exe"));

            // Check for specific watcher processes
            const watcherNames = ["gmail_watcher", "linkedin", "whatsapp", "orchestrator"];

            for (const watcher of watcherNames) {
                const isRunning = processes.some((p: string) => p.includes(watcher));
                services.push({
                    name: watcher,
                    status: isRunning ? "running" : "stopped",
                    uptime: isRunning ? "N/A" : undefined,
                    pid: isRunning ? undefined : undefined,
                });
            }
        } catch (error) {
            console.error("Error checking processes:", error);
        }

        // Read recent logs
        const logsPath = path.join(VAULT_PATH, "Logs");
        let recentLogs: string[] = [];

        try {
            const logFiles = await fs.readdir(logsPath);
            const latestLog = logFiles.sort().reverse()[0];

            if (latestLog) {
                const logContent = await fs.readFile(path.join(logsPath, latestLog), "utf-8");
                recentLogs = logContent.split("\n").slice(-20);
            }
        } catch (error) {
            console.error("Error reading logs:", error);
        }

        return NextResponse.json(
            { running, services, recentLogs, _timestamp: Date.now() },
            {
                headers: {
                    'Cache-Control': 'no-store, no-cache, must-revalidate',
                    'Pragma': 'no-cache',
                }
            }
        );
    } catch (error) {
        console.error("Error getting FTE status:", error);
        return NextResponse.json({ running: false, services: [], recentLogs: [] }, { status: 500 });
    }
}
