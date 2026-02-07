import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";

const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const VAULT_PATH = path.join(PROJECT_ROOT, "AI_Employee_Vault");

export const dynamic = 'force-dynamic';

export async function GET() {
    try {
        const logsPath = path.join(VAULT_PATH, "Logs");
        const logs: Array<{
            id: string;
            timestamp: string;
            time: string;
            level: string;
            source: string;
            message: string;
        }> = [];

        try {
            const files = await fs.readdir(logsPath);

            // First, try to read JSON log files (structured logs from orchestrator)
            const jsonLogFiles = files.filter(f => f.endsWith(".json")).sort().reverse();

            if (jsonLogFiles.length > 0) {
                // Read today's JSON log file
                const latestJsonLog = path.join(logsPath, jsonLogFiles[0]);
                const content = await fs.readFile(latestJsonLog, "utf-8");
                const lines = content.split("\n").filter(line => line.trim());

                // Parse each JSON line (last 100 entries)
                for (const line of lines.slice(-100)) {
                    try {
                        const entry = JSON.parse(line);
                        const timestamp = entry.timestamp || new Date().toISOString();
                        const time = new Date(timestamp).toLocaleTimeString("en-US", {
                            hour: "2-digit",
                            minute: "2-digit",
                            second: "2-digit",
                            hour12: false
                        });

                        logs.push({
                            id: `${Date.now()}_${Math.random()}`,
                            timestamp,
                            time,
                            level: (entry.level || "info").toLowerCase(),
                            source: entry.logger || "system",
                            message: entry.message || "",
                        });
                    } catch {
                        // Skip malformed JSON lines
                    }
                }
            }

            // Fallback to .log files if no JSON logs found
            if (logs.length === 0) {
                const logFiles = files.filter(f => f.endsWith(".log") || f.endsWith(".txt")).sort().reverse();

                if (logFiles.length > 0) {
                    const latestLogPath = path.join(logsPath, logFiles[0]);
                    const content = await fs.readFile(latestLogPath, "utf-8");
                    const lines = content.split("\n").filter(line => line.trim());

                    for (const line of lines.slice(-100)) {
                        let level = "info";
                        const time = new Date().toLocaleTimeString();

                        if (line.toLowerCase().includes("error")) level = "error";
                        else if (line.toLowerCase().includes("warn")) level = "warn";
                        else if (line.toLowerCase().includes("success")) level = "success";

                        const sourceMatch = line.match(/\[([^\]]+)\]/);
                        const source = sourceMatch ? sourceMatch[1] : "system";

                        logs.push({
                            id: `${Date.now()}_${Math.random()}`,
                            timestamp: new Date().toISOString(),
                            time,
                            level,
                            source,
                            message: line.substring(0, 200),
                        });
                    }
                }
            }
        } catch (error) {
            console.error("Error reading log files:", error);
        }

        return NextResponse.json(
            { logs: logs.reverse(), _timestamp: Date.now() },
            {
                headers: {
                    'Cache-Control': 'no-store, no-cache, must-revalidate',
                    'Pragma': 'no-cache',
                }
            }
        );
    } catch (error) {
        console.error("Error getting logs:", error);
        return NextResponse.json({ logs: [] }, { status: 500 });
    }
}
