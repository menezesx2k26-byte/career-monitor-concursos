# 🛰️ Monitor de Concursos e Oportunidades Públicas

Monitor redundante para acompanhar publicações oficiais relevantes, detectar mudanças e reduzir o risco de perder convocações, nomeações, resultados, homologações ou documentos importantes.

> **Estado atual:** o repositório mantém o motor Python, a configuração das fontes e um detector independente em Cloudflare Workers. Os workflows do GitHub Actions foram removidos em setembro de 2026; o GitHub não deve mais ser tratado como scheduler ativo deste projeto.

## 🎯 Objetivo

Transformar fontes oficiais dispersas em um acompanhamento verificável, com foco em:

- São Vicente — Concurso nº 02/2026;
- Praia Grande — Concurso nº 004/2024 / ACS;
- páginas de convocações e resultados;
- diários e boletins oficiais;
- documentos e PDFs relacionados aos processos monitorados.

A regra principal é simples: **silêncio só é confiável quando o monitor está saudável**.

## 🧭 Arquitetura atual

```text
Fontes oficiais
   │
   ├── Motor Python
   │   ├── monitor.py
   │   ├── monitor_runner.py
   │   ├── deep_audit.py
   │   └── search_probe.py
   │
   └── Cloudflare Worker
       ├── scheduler independente
       ├── estado persistente
       ├── matching próprio
       └── health/observabilidade
```

O Worker está configurado para executar nos minutos **02, 17, 32 e 47 de cada hora**.

Os scripts Python continuam no repositório para execução manual ou por infraestrutura externa. Como não há mais workflows em `.github/workflows`, qualquer documentação histórica que descreva GitHub Actions como executor principal deve ser considerada legado.

## 🔎 Fontes monitoradas

### São Vicente

- página oficial do Concurso nº 02/2026;
- IBAM/SP do Concurso nº 02/2026;
- página oficial de convocações de 2026;
- Boletim Oficial do Município.

### Praia Grande

- página oficial de concursos e processos seletivos;
- Diário Oficial Eletrônico;
- Concurso nº 004/2024, com foco em Agente Comunitário de Saúde.

A configuração vigente está em:

```text
config/sources.json
```

## 🧠 Como a detecção funciona

Cada fonte possui regras próprias de contexto, termos obrigatórios e gatilhos. O monitor evita depender apenas de busca textual simples.

Entre os eventos relevantes estão:

- classificação e resultado;
- homologação;
- convocação;
- nomeação;
- posse;
- reclassificação;
- exame admissional;
- entrega de documentos;
- atos que tornem convocações sem efeito.

Quando documentos relacionados são encontrados, o sistema pode tratá-los separadamente para reduzir falsos negativos.

## ☁️ Cloudflare Worker

O detector redundante vive em:

```text
cloudflare/
```

Configuração principal:

```text
cloudflare/wrangler.jsonc
```

Características atuais:

- cron independente;
- observabilidade habilitada;
- estado persistente via binding `WATCH_STATE` quando provisionado;
- endpoints operacionais definidos pelo Worker;
- execução desacoplada do GitHub Actions.

## 🛠️ Execução local do motor Python

Crie um ambiente Python e instale as dependências:

```bash
python -m venv .venv
pip install -r requirements.txt
```

Depois use o runner ou os scripts de auditoria conforme a necessidade:

```bash
python monitor_runner.py
python deep_audit.py
```

Consulte os próprios scripts e arquivos de configuração antes de automatizar uma execução em produção.

## 🔐 Segurança e privacidade

Este repositório pode ser público, portanto:

- não commitar tokens ou chaves;
- não armazenar números de inscrição ou identificadores pessoais em texto aberto;
- não publicar credenciais de Telegram, ntfy, e-mail ou Cloudflare;
- usar secrets/variáveis apenas na infraestrutura que realmente executa o monitor;
- revisar qualquer novo canal de alerta antes de ativá-lo.

## ✅ Princípios operacionais

1. **Fonte oficial primeiro.**
2. **Nenhuma mudança relevante deve depender de um único parser.**
3. **Falha de extração também é um evento observável.**
4. **Estado e baseline devem impedir alertas massivos na primeira execução.**
5. **Monitor morto não pode parecer “nenhuma novidade”.**
6. **Documentação deve refletir o runtime real, não uma arquitetura antiga.**

## 📁 Estrutura principal

```text
android/              integração/cliente Android
cloudflare/           detector redundante em Workers
config/               fontes e regras de monitoramento
docs/                 documentação operacional e histórica
scripts/              utilitários
state/                estado local/versionado quando aplicável
tests/                testes do monitor
monitor.py            motor principal
monitor_runner.py     orquestração de execução
deep_audit.py         auditoria aprofundada
search_probe.py       sondas de busca
smtp_alert.py         integração de alerta por e-mail
```

## 📌 Nota sobre documentação legada

Parte de `docs/` foi escrita quando GitHub Actions ainda fazia parte da arquitetura. Antes de seguir instruções antigas de deploy ou watchdog, confirme se elas ainda correspondem ao runtime atual.

---

**Status:** ativo em evolução. O código deve continuar favorecendo redundância, rastreabilidade e fontes oficiais. 🛡️