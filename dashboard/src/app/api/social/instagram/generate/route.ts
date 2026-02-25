import { NextResponse } from "next/server";
import { buildInstagramQwenPrompt, runQwenPrompt } from "@/lib/qwen";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const topicPrompt = String(body?.prompt || "").trim();
        const seedCaption = String(body?.seedCaption || "").trim();

        if (!topicPrompt) {
            return NextResponse.json(
                { success: false, error: "prompt is required" },
                { status: 400 }
            );
        }

        const prompt = buildInstagramQwenPrompt(topicPrompt, seedCaption);
        const generatedContent = await runQwenPrompt(prompt);

        return NextResponse.json({
            success: true,
            engine: "qwen",
            generatedContent,
        });
    } catch (error) {
        return NextResponse.json(
            {
                success: false,
                error: error instanceof Error ? error.message : "Qwen generation failed",
            },
            { status: 500 }
        );
    }
}
