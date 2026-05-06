# Microambiental — Dashboard de Marketing

Snapshot semanal de Google Ads, Google Analytics 4 e SE Ranking.

## Stack
- HTML estático (sem build)
- Chart.js via CDN
- Vercel Serverless Function (`api/unlock.js`) para gate de senha

## Deploy
Conectado ao Vercel. A variável de ambiente `DASHBOARD_PASSWORD` precisa estar configurada no projeto Vercel.

## Atualização
Os dados em `data/snapshot.json` são regenerados pela rotina semanal `week-mkt-report` rodando localmente via Cowork/Claude. Cada push neste repo dispara redeploy no Vercel.
