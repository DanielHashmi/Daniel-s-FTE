import { NextResponse } from "next/server";
import { cookies } from "next/headers";

const SESSION_SECRET = process.env.SESSION_SECRET || "daniel-fte-secret-2026";

export async function GET() {
    const cookieStore = await cookies();
    const session = cookieStore.get("fte-session");

    if (!session?.value) {
        return NextResponse.json({ authenticated: false }, { status: 401 });
    }

    try {
        const decoded = Buffer.from(session.value, "base64").toString();
        if (decoded.startsWith(SESSION_SECRET)) {
            return NextResponse.json({ authenticated: true, user: "Daniel" });
        }
    } catch {
        // Invalid token
    }

    return NextResponse.json({ authenticated: false }, { status: 401 });
}
