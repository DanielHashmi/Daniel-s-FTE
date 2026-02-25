import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const DASHBOARD_PASSWORD = process.env.DASHBOARD_PASSWORD || "danielsecurepassfornow";
const SESSION_SECRET = process.env.SESSION_SECRET || "daniel-fte-secret-2026";

export async function POST(request: NextRequest) {
    try {
        const { password } = await request.json();

        if (password === DASHBOARD_PASSWORD) {
            // Create a simple session token
            const token = Buffer.from(`${SESSION_SECRET}:${Date.now()}`).toString("base64");

            const cookieStore = await cookies();
            cookieStore.set("fte-session", token, {
                httpOnly: true,
                secure: process.env.NODE_ENV === "production",
                sameSite: "lax",
                maxAge: 60 * 60 * 24 * 7, // 7 days
                path: "/",
            });

            return NextResponse.json({ success: true });
        }

        return NextResponse.json({ error: "Invalid password" }, { status: 401 });
    } catch {
        return NextResponse.json({ error: "Invalid request" }, { status: 400 });
    }
}
