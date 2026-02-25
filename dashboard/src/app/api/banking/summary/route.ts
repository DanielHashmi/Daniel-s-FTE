import { NextResponse } from 'next/server';
import * as fs from 'fs';
import * as path from 'path';

const VAULT_PATH = path.join(process.cwd(), '..', 'AI_Employee_Vault', 'Banking');

export const dynamic = 'force-dynamic';

export async function GET() {
    try {
        const summaryPath = path.join(VAULT_PATH, 'summary.json');
        const transactionsPath = path.join(VAULT_PATH, 'transactions.json');

        let summary = {
            current_balance: 0,
            total_income: 0,
            total_expenses: 0,
            net_profit: 0,
            transaction_count: 0,
            is_mock_data: true,
            generated_at: new Date().toISOString()
        };

        let transactions: any[] = [];

        // Read summary
        if (fs.existsSync(summaryPath)) {
            const data = fs.readFileSync(summaryPath, 'utf-8');
            summary = JSON.parse(data);
        }

        // Read transactions
        if (fs.existsSync(transactionsPath)) {
            const data = fs.readFileSync(transactionsPath, 'utf-8');
            transactions = JSON.parse(data);
        }

        return NextResponse.json({
            success: true,
            summary,
            transactions: transactions.slice(0, 20), // Last 20 transactions
            isMockData: summary.is_mock_data || true
        });

    } catch (error) {
        console.error('Banking API error:', error);
        return NextResponse.json({
            success: false,
            error: 'Failed to load banking data',
            summary: {
                current_balance: 0,
                total_income: 0,
                total_expenses: 0,
                net_profit: 0
            },
            transactions: [],
            isMockData: true
        });
    }
}
