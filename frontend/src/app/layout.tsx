import "./globals.css";
import type { Metadata } from "next";
import { Hanken_Grotesk, DM_Mono } from "next/font/google";
import { Providers } from "@/components/providers";

const sans = Hanken_Grotesk({ subsets: ["latin"], variable: "--font-sans" });
const mono = DM_Mono({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "Nexora —— 企业级 Agent 平台 (Ragent AI)",
  description: "LangGraph + LangChain + Milvus + MCP + Langfuse",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning className={`${sans.variable} ${mono.variable}`}>
      <body className="font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
