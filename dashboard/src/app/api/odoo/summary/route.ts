import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(process.cwd(), "..");
const VAULT_PATH = path.join(PROJECT_ROOT, "AI_Employee_Vault");
const PYTHON_EXE = process.env.PYTHON_EXE || "python";

export const dynamic = 'force-dynamic';
export const revalidate = 0;

// Track last sync time to avoid syncing too frequently
let lastSyncTime = 0;
const SYNC_INTERVAL = 30000; // Sync every 30 seconds max

async function syncOdoo(): Promise<boolean> {
    const now = Date.now();
    if (now - lastSyncTime < SYNC_INTERVAL) {
        return false; // Skip sync, too recent
    }

    try {
        const scriptPath = path.join(PROJECT_ROOT, ".claude", "skills", "odoo-accounting", "scripts", "main_operation.py");
        await execAsync(`${PYTHON_EXE} "${scriptPath}" --mode draft sync`, {
            cwd: PROJECT_ROOT,
            timeout: 15000 // 15 second timeout
        });
        lastSyncTime = now;
        return true;
    } catch (error) {
        console.error("Auto-sync failed:", error);
        return false;
    }
}

export async function GET(request: Request) {
    try {
        // Check if auto-sync is requested (default: true)
        const url = new URL(request.url);
        const autoSync = url.searchParams.get('autoSync') !== 'false';

        // Auto-sync with Odoo before reading (if enabled and interval passed)
        if (autoSync) {
            await syncOdoo();
        }

        const stats = {
            revenue: 0,
            expenses: 0,
            pendingInvoices: 0,
            overdueInvoices: 0,
        };

        const transactions: Array<{id: number; date: string; description: string; amount: number; type: string; status: string}> = [];
        const invoices: Array<{id: string; client: string; amount: number; status: string; dueDate: string}> = [];

        // Determine current month path
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const monthDir = `${year}-${month}`;

        const transactionsFile = path.join(VAULT_PATH, "Accounting", "transactions", monthDir, "transactions.json");

        try {
            // Read JSON directly (will throw if doesn't exist)
            const content = await fs.readFile(transactionsFile, "utf-8");
            const data = JSON.parse(content);

            if (data.transactions && Array.isArray(data.transactions)) {
                for (const txn of data.transactions) {
                    transactions.push(txn);

                    if (txn.type === 'income') {
                        stats.revenue += txn.amount;
                    } else if (txn.type === 'expense') {
                        stats.expenses += txn.amount;
                    }
                }
            }
        } catch (error) {
            console.log("Odoo transactions file not found:", transactionsFile);
        }

        return NextResponse.json(
            { stats, transactions, invoices, _timestamp: Date.now(), _lastSync: lastSyncTime },
            {
                headers: {
                    'Cache-Control': 'no-store, no-cache, must-revalidate',
                    'Pragma': 'no-cache',
                }
            }
        );
    } catch (error) {
        console.error("Error getting Odoo summary:", error);
        return NextResponse.json({
            stats: { revenue: 0, expenses: 0, pendingInvoices: 0, overdueInvoices: 0 },
            transactions: [],
            invoices: []
        }, { status: 500 });
    }
}
