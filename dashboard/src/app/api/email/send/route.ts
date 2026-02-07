import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import matter from "gray-matter";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const VAULT_PATH = path.join(PROJECT_ROOT, "AI_Employee_Vault");

export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
    try {
        const { id } = await request.json();

        if (!id) {
            return NextResponse.json({
                success: false,
                error: "Email ID required"
            }, { status: 400 });
        }

        // Find email in Approved folder
        const approvedPath = path.join(VAULT_PATH, "Approved");
        const files = await fs.readdir(approvedPath);

        let emailFile = "";
        let emailData: any = null;

        for (const file of files) {
            if (!file.endsWith(".md")) continue;

            const filePath = path.join(approvedPath, file);
            const content = await fs.readFile(filePath, "utf-8");
            const { data } = matter(content);

            if (data.id === id) {
                emailFile = file;
                emailData = data;
                break;
            }
        }

        if (!emailFile || !emailData) {
            return NextResponse.json({
                success: false,
                error: "Email not found in Approved folder"
            }, { status: 404 });
        }

        // Extract email details
        const to = emailData.metadata?.to || emailData.to;
        const subject = emailData.metadata?.subject || emailData.subject;
        const filePath = path.join(approvedPath, emailFile);
        const fullContent = await fs.readFile(filePath, "utf-8");
        const { content: body } = matter(fullContent);

        // Extract actual email content (remove markdown headers)
        const contentMatch = body.match(/## Content\s+([\s\S]*?)(?=\n\n---|$)/);
        const emailBody = contentMatch ? contentMatch[1].trim() : body.trim();

        if (!to || !subject || !emailBody) {
            return NextResponse.json({
                success: false,
                error: "Missing required email fields (to, subject, or body)"
            }, { status: 400 });
        }

        // Use email-ops skill to send
        try {
            const skillPath = path.join(PROJECT_ROOT, ".claude", "skills", "email-ops", "scripts", "main_operation.py");

            // Escape arguments for shell
            const escapedTo = to.replace(/"/g, '\\"');
            const escapedSubject = subject.replace(/"/g, '\\"');
            const escapedBody = emailBody.replace(/"/g, '\\"').replace(/\n/g, '\\n');

            // Execute email send with proper arguments
            const cmd = `python "${skillPath}" --action send --to "${escapedTo}" --subject "${escapedSubject}" --body "${escapedBody}"`;

            console.log("Executing email send command");

            // Read .env to get DRY_RUN setting
            let envVars: any = { ...process.env };
            try {
                const envPath = path.join(PROJECT_ROOT, ".env");
                const envContent = await fs.readFile(envPath, "utf-8");
                const lines = envContent.split("\n");
                for (const line of lines) {
                    const trimmed = line.trim();
                    if (trimmed && !trimmed.startsWith("#") && trimmed.includes("=")) {
                        const [key, ...valueParts] = trimmed.split("=");
                        const value = valueParts.join("=").trim();
                        envVars[key.trim()] = value;
                    }
                }
            } catch (e) {
                console.error("Error reading .env:", e);
            }

            const { stdout, stderr } = await execAsync(cmd, {
                cwd: PROJECT_ROOT,
                timeout: 30000,
                env: envVars
            });

            console.log("Email send stdout:", stdout);
            if (stderr) console.log("Email send stderr:", stderr);

            // Check for errors (but ignore UserWarnings)
            if (stderr && !stderr.includes("UserWarning") && stderr.toLowerCase().includes("error")) {
                throw new Error(stderr);
            }

            // Check if send was successful
            if (!stdout.includes("[OK]") && !stdout.toLowerCase().includes("success") && !stdout.toLowerCase().includes("logged")) {
                throw new Error("Email send did not confirm success");
            }

            // Move to Done folder
            const donePath = path.join(VAULT_PATH, "Done", emailFile);
            await fs.rename(filePath, donePath);

            return NextResponse.json({
                success: true,
                message: "Email sent successfully",
                details: stdout.trim()
            });

        } catch (error: any) {
            console.error("Error sending email:", error);
            return NextResponse.json({
                success: false,
                error: error.message || "Failed to send email"
            }, { status: 500 });
        }

    } catch (error) {
        console.error("Error in send endpoint:", error);
        return NextResponse.json({
            success: false,
            error: "Failed to process send request"
        }, { status: 500 });
    }
}
