import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import { VAULT_PATH } from "@/lib/vault";

type WhatsAppWebhookPayload = {
  entry?: Array<{
    changes?: Array<{
      field?: string;
      value?: {
        metadata?: {
          phone_number_id?: string;
          display_phone_number?: string;
        };
        contacts?: Array<{
          wa_id?: string;
          profile?: {
            name?: string;
          };
        }>;
        messages?: Array<{
          id?: string;
          from?: string;
          timestamp?: string;
          type?: string;
          text?: {
            body?: string;
          };
        }>;
      };
    }>;
  }>;
};

function normalizeDomain(raw: string): string {
  const value = String(raw || "").trim().toLowerCase();
  return value || "personal";
}

function toSafeToken(raw: string): string {
  const safe = String(raw || "")
    .trim()
    .replace(/[^A-Za-z0-9_-]+/g, "_")
    .replace(/^_+|_+$/g, "");
  return safe || `msg_${Date.now()}`;
}

function quoteYaml(raw: string): string {
  return `"${String(raw || "").replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
}

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const mode = url.searchParams.get("hub.mode");
  const token = url.searchParams.get("hub.verify_token");
  const challenge = url.searchParams.get("hub.challenge");
  const expectedToken = String(process.env.WHATSAPP_VERIFY_TOKEN || "").trim();

  if (!expectedToken) {
    return NextResponse.json(
      { success: false, error: "WHATSAPP_VERIFY_TOKEN is not configured" },
      { status: 500 },
    );
  }

  if (mode === "subscribe" && challenge && token === expectedToken) {
    return new Response(challenge, {
      status: 200,
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  }

  return NextResponse.json({ success: false, error: "Webhook verification failed" }, { status: 403 });
}

export async function POST(request: Request) {
  let payload: WhatsAppWebhookPayload;
  try {
    payload = (await request.json()) as WhatsAppWebhookPayload;
  } catch {
    return NextResponse.json({ success: false, error: "Invalid JSON payload" }, { status: 400 });
  }

  const targetDomain = normalizeDomain(process.env.WHATSAPP_WEBHOOK_DOMAIN || "personal");
  const targetDir = path.join(VAULT_PATH, "Needs_Action", targetDomain);
  await fs.mkdir(targetDir, { recursive: true });

  let createdCount = 0;

  for (const entry of payload.entry || []) {
    for (const change of entry.changes || []) {
      if (change.field !== "messages") continue;

      const value = change.value || {};
      const metadata = value.metadata || {};
      const contactsByWaId = new Map<string, string>();
      for (const contact of value.contacts || []) {
        const waId = String(contact.wa_id || "").trim();
        const name = String(contact.profile?.name || "").trim();
        if (waId) {
          contactsByWaId.set(waId, name || "Unknown");
        }
      }

      for (const message of value.messages || []) {
        if (String(message.type || "").toLowerCase() !== "text") continue;
        const textBody = String(message.text?.body || "").trim();
        if (!textBody) continue;

        const rawMessageId = String(message.id || "").trim();
        const messageId = toSafeToken(rawMessageId || `wa_${Date.now()}`);
        const senderWaId = String(message.from || "").trim();
        const senderName = contactsByWaId.get(senderWaId) || "Unknown";
        const fileName = `WHATSAPP_${messageId}.md`;
        const filePath = path.join(targetDir, fileName);

        try {
          await fs.access(filePath);
          continue;
        } catch {
          // File does not exist yet; continue creation.
        }

        const createdAtIso = new Date().toISOString();
        const frontmatter = [
          "---",
          `id: ${quoteYaml(messageId)}`,
          "type: message",
          "source: whatsapp_cloud_api",
          "platform: whatsapp",
          "status: pending",
          "priority: high",
          `domain: ${targetDomain}`,
          `created: ${createdAtIso}`,
          "metadata:",
          `  sender: ${quoteYaml(senderName)}`,
          `  sender_wa_id: ${quoteYaml(senderWaId)}`,
          `  message_id: ${quoteYaml(rawMessageId || messageId)}`,
          `  wa_phone_number_id: ${quoteYaml(String(metadata.phone_number_id || ""))}`,
          `  wa_display_phone_number: ${quoteYaml(String(metadata.display_phone_number || ""))}`,
          "---",
          "",
        ].join("\n");

        const body = [
          "# Incoming WhatsApp Message",
          "",
          `**From:** ${senderName}`,
          "",
          "## Message",
          textBody,
          "",
        ].join("\n");

        await fs.writeFile(filePath, `${frontmatter}${body}`, "utf-8");
        createdCount += 1;
      }
    }
  }

  return NextResponse.json({ success: true, created: createdCount });
}
