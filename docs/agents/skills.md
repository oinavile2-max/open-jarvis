# Skills de engenharia do JARVIS

Pacote Matt Pocock Skills **v1.3.1**, fixado na [release oficial](https://github.com/mattpocock/skills/releases/tag/v1.3.1).

As 27 skills estáveis são as mesmas listadas pelo plugin oficial. Cada pasta inclui os arquivos auxiliares originais.

Codex encontra os arquivos em `.agents/skills/`; Claude Code encontra suas cópias em `.claude/skills/`. As duas árvores são idênticas. São cópias de arquivos comuns para funcionar no Windows sem links simbólicos. Evite instalar também outra cópia do mesmo pacote no mesmo agente.

Abra o repositório na ferramenta correspondente e inicie uma nova sessão para atualizar a descoberta das skills. O projeto contém as skills; a instalação de Codex/Claude Code e autenticação são próprias de cada ferramenta.

Leia `AGENTS.md` e os documentos de `docs/agents/` antes de aplicar um fluxo. Skills marcadas como **pedido explícito** devem ser iniciadas pelo usuário. As demais podem ser selecionadas conforme a tarefa. Leia o `SKILL.md` completo antes de usá-lo.

## Catálogo

| Skill | Acionamento | Arquivo |
|---|---|---|
| `ask-matt` | Pedido explícito | [SKILL.md](../../.agents/skills/ask-matt/SKILL.md) |
| `diagnosing-bugs` | Conforme a tarefa | [SKILL.md](../../.agents/skills/diagnosing-bugs/SKILL.md) |
| `grill-with-docs` | Pedido explícito | [SKILL.md](../../.agents/skills/grill-with-docs/SKILL.md) |
| `triage` | Pedido explícito | [SKILL.md](../../.agents/skills/triage/SKILL.md) |
| `improve-codebase-architecture` | Pedido explícito | [SKILL.md](../../.agents/skills/improve-codebase-architecture/SKILL.md) |
| `setup-matt-pocock-skills` | Pedido explícito | [SKILL.md](../../.agents/skills/setup-matt-pocock-skills/SKILL.md) |
| `tdd` | Conforme a tarefa | [SKILL.md](../../.agents/skills/tdd/SKILL.md) |
| `to-spec` | Pedido explícito | [SKILL.md](../../.agents/skills/to-spec/SKILL.md) |
| `to-tickets` | Pedido explícito | [SKILL.md](../../.agents/skills/to-tickets/SKILL.md) |
| `wayfinder` | Pedido explícito | [SKILL.md](../../.agents/skills/wayfinder/SKILL.md) |
| `implement` | Pedido explícito | [SKILL.md](../../.agents/skills/implement/SKILL.md) |
| `implement-spec` | Pedido explícito | [SKILL.md](../../.agents/skills/implement-spec/SKILL.md) |
| `prototype` | Conforme a tarefa | [SKILL.md](../../.agents/skills/prototype/SKILL.md) |
| `research` | Conforme a tarefa | [SKILL.md](../../.agents/skills/research/SKILL.md) |
| `domain-modeling` | Conforme a tarefa | [SKILL.md](../../.agents/skills/domain-modeling/SKILL.md) |
| `codebase-design` | Conforme a tarefa | [SKILL.md](../../.agents/skills/codebase-design/SKILL.md) |
| `code-review` | Conforme a tarefa | [SKILL.md](../../.agents/skills/code-review/SKILL.md) |
| `pr` | Conforme a tarefa | [SKILL.md](../../.agents/skills/pr/SKILL.md) |
| `retro` | Pedido explícito | [SKILL.md](../../.agents/skills/retro/SKILL.md) |
| `wizard` | Conforme a tarefa | [SKILL.md](../../.agents/skills/wizard/SKILL.md) |
| `grill-me` | Pedido explícito | [SKILL.md](../../.agents/skills/grill-me/SKILL.md) |
| `grilling` | Conforme a tarefa | [SKILL.md](../../.agents/skills/grilling/SKILL.md) |
| `handoff` | Pedido explícito | [SKILL.md](../../.agents/skills/handoff/SKILL.md) |
| `teach` | Pedido explícito | [SKILL.md](../../.agents/skills/teach/SKILL.md) |
| `to-questionnaire` | Pedido explícito | [SKILL.md](../../.agents/skills/to-questionnaire/SKILL.md) |
| `wait-what` | Pedido explícito | [SKILL.md](../../.agents/skills/wait-what/SKILL.md) |
| `writing-for-agents` | Conforme a tarefa | [SKILL.md](../../.agents/skills/writing-for-agents/SKILL.md) |

## Fluxo do projeto

Requisitos e vocabulário → especificação quando necessária → implementação em partes verificáveis → diagnóstico e testes relevantes → revisão → compilação quando solicitada. Use apenas as etapas úteis à tarefa.

Não confunda essas skills de desenvolvimento com ferramentas MCP do assistente em execução. O JARVIS mantém seu próprio fluxo Claude/MCP; este pacote orienta os agentes que trabalham no código.

## Integridade e atualização

Licença e manifesto estão em `third_party/mattpocock-skills/`. O manifesto registra o caminho original e SHA-256 de cada arquivo. Atualizações devem ser explícitas e manter as duas árvores sincronizadas. Nenhum instalador ou script do pacote é executado automaticamente.

