import { NextRequest, NextResponse } from "next/server";

const SESSION_SECRET = process.env.SESSION_SECRET || "daniel-fte-secret-2026";
const SESSION_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;

function hasValidSessionToken(token?: string): boolean {
    if (!token) return false;

    try {
        const decoded = atob(token);
        const prefix = `${SESSION_SECRET}:`;

        if (!decoded.startsWith(prefix)) {
            return false;
        }

        const issuedAt = Number(decoded.slice(prefix.length));
        if (!Number.isFinite(issuedAt)) {
            return false;
        }

        return Date.now() - issuedAt <= SESSION_MAX_AGE_MS;
    } catch {
        return false;
    }
}

export function middleware(request: NextRequest) {
    const { pathname, search } = request.nextUrl;
    const token = request.cookies.get("fte-session")?.value;
    const isAuthenticated = hasValidSessionToken(token);

    if (pathname.startsWith("/api/auth")) {
        return NextResponse.next();
    }

    if (pathname === "/") {
        if (isAuthenticated) {
            return NextResponse.redirect(new URL("/dashboard", request.url));
        }
        return NextResponse.next();
    }

    if (pathname.startsWith("/api")) {
        if (isAuthenticated) {
            return NextResponse.next();
        }
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    if (pathname.startsWith("/dashboard")) {
        if (isAuthenticated) {
            return NextResponse.next();
        }
        const loginUrl = new URL("/", request.url);
        loginUrl.searchParams.set("next", `${pathname}${search}`);
        return NextResponse.redirect(loginUrl);
    }

    return NextResponse.next();
}

export const config = {
    matcher: ["/", "/dashboard/:path*", "/api/:path*"],
};
