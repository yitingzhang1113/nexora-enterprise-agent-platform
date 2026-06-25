import Link from "next/link";

export default function Home() {
  return (
    <div className="container">
      <div className="card">
        <h1>💊 Nexora —— 医药知识 Agent / RAG 平台</h1>
        <p className="muted">
          仿 Onyx 架构的学习型项目：FastAPI + Postgres/pgvector + Celery + Ollama。
          上传医药资料 → 自动切块/嵌入/索引 → 用中文问答，回答带可溯源引用。
        </p>
        <div className="row" style={{ marginTop: 16 }}>
          <Link href="/chat"><button>开始聊天</button></Link>
          <Link href="/documents"><button className="secondary">管理文档</button></Link>
          <Link href="/assistants"><button className="secondary">配置助手</button></Link>
        </div>
      </div>

      <div className="card">
        <h3>架构一览</h3>
        <ul className="muted">
          <li>检索：pgvector 向量 + Postgres 全文，RRF 融合 (混合检索)</li>
          <li>生成：本地 Ollama (可一键切换 Claude)</li>
          <li>Agent：search_docs / calculator 工具调用循环</li>
          <li>异步索引：Celery + Redis</li>
        </ul>
      </div>
    </div>
  );
}
