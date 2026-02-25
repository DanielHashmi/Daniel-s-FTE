import { NextResponse } from "next/server";

export const dynamic = 'force-dynamic';

export async function GET() {
    // Check if Odoo is connected
    const connected = !!(process.env.ODOO_URL && process.env.ODOO_API_KEY);

    // Return mock data - real implementation would use Odoo API
    const invoices = connected
        ? [
            {
                id: "INV-001",
                partner: "Acme Corp",
                amount: 5000,
                currency: "USD",
                status: "draft" as const,
                date: new Date().toLocaleDateString(),
            },
            {
                id: "INV-002",
                partner: "TechStart Inc",
                amount: 12500,
                currency: "USD",
                status: "posted" as const,
                date: new Date().toLocaleDateString(),
            },
            {
                id: "INV-003",
                partner: "Global Services",
                amount: 3200,
                currency: "USD",
                status: "paid" as const,
                date: new Date().toLocaleDateString(),
            },
        ]
        : [];

    const totalRevenue = invoices
        .filter((i) => i.status === "paid")
        .reduce((sum, i) => sum + i.amount, 0);
    const pendingInvoices = invoices.filter((i) => i.status === "draft").length;
    const paidInvoices = invoices.filter((i) => i.status === "paid").length;

    return NextResponse.json({
        connected,
        invoices,
        totalRevenue,
        pendingInvoices,
        paidInvoices,
    });
}
