import type { Metadata } from "next";
import { ToastProvider } from "@/context/ToastContext";
import "./globals.css";

export const metadata: Metadata = {
  title: "AegisAI Agent Governance Control Plane",
  description:
    "Enterprise AI production platform for multi-agent orchestration, policy simulation, HITL, evals, telemetry, and audit governance."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <ToastProvider>{children}</ToastProvider>
      </body>
    </html>
  );
}
