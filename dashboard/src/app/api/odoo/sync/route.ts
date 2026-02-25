import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import path from "path";

const execAsync = promisify(exec);
const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const PYTHON_EXE = process.env.PYTHON_EXE || "python";

export async function POST() {
    try {
        const scriptPath = path.join(PROJECT_ROOT, ".claude", "skills", "odoo-accounting", "scripts", "main_operation.py");

        // Execute python script
        const cmd = `${PYTHON_EXE} "${scriptPath}" --mode draft sync`;
        console.log(`Executing Odoo sync: ${cmd}`);

        const { stdout, stderr } = await execAsync(cmd, { cwd: PROJECT_ROOT });

        if (stderr && !stderr.includes("UserWarning")) {
            console.warn("Odoo sync stderr:", stderr);
        }

        return NextResponse.json({
            success: true,
            message: "Odoo sync completed",
            details: stdout
        });

    } catch (error: any) {
        console.error("Odoo sync failed:", error);
        return NextResponse.json({
            success: false,
            error: error.message || "Odoo sync failed"
        }, { status: 500 });
    }
}
