-- 为 Langfuse 创建独立数据库 (与应用库分开, 避免表名冲突如 traces)
SELECT 'CREATE DATABASE langfuse'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'langfuse')\gexec
