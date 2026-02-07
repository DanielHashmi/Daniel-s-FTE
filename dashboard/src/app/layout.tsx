import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Daniel FTE | Personal AI Employee",
  description: "Your autonomous AI employee for email, social media, and business operations",
  keywords: ["AI", "Employee", "Automation", "Dashboard", "FTE"],
  authors: [{ name: "Daniel" }],
  viewport: "width=device-width, initial-scale=1",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f8fafc" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0a0f" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
