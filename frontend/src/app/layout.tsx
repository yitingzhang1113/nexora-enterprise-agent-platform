import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Nexora —— 医药 Agent / RAG 平台",
  description: "仿 Onyx 的学习型企业级 Agent 平台",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>
        <nav className="nav">
          <span className="brand">💊 Nexora</span>
          <Link href="/chat">聊天</Link>
          <Link href="/documents">文档</Link>
          <Link href="/assistants">助手</Link>
          <span style={{ flex: 1 }} />
          <span className="muted">学习型 · 医药 domain</span>
        </nav>
        {children}
      </body>
    </html>
  );
}
