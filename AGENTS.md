# JARVIS OS Windows — instruções de desenvolvimento

## Regras do projeto

- Use português brasileiro na comunicação com o usuário e nos textos da interface.
- Preserve o visual aprovado e os comportamentos existentes ao corrigir outra área.
- Priorize baixa latência, streaming e interrupção natural da fala. Não afirme melhorias de desempenho sem evidências.
- Execute apenas compilações solicitadas pelo usuário para a entrega em andamento. Uma autorização anterior não inicia builds futuros automaticamente.
- Nunca inclua chaves pessoais, credenciais, fotos cadastradas ou memória de usuário nos commits e pacotes.
- Confirme resultados reais de ferramentas antes de afirmar que uma ação foi executada.
- Exibir uma foto cadastrada não autentica identidade. Não transforme correspondência facial local em autenticação do Windows.
- Faça testes proporcionais ao risco. Diferencie testes locais, testes do EXE e validação real de microfone, APIs, câmera e dispositivos.

## Agent skills

O pacote Matt Pocock Skills v1.3.1 está instalado por projeto. Codex: `.agents/skills/`; Claude Code: `.claude/skills/`. Catálogo e origem: `docs/agents/skills.md`.

Selecione as skills pertinentes e leia seus arquivos completos antes de aplicá-las. Respeite a distinção entre acionamento automático e pedido explícito. As instruções do usuário prevalecem sobre os fluxos das skills. Use o contexto existente para escolhas rotineiras já autorizadas e peça esclarecimentos apenas quando houver informação realmente necessária.

### Issue tracker

GitHub `oinavile2-max/open-jarvis`. Veja `docs/agents/issue-tracker.md`. Não publique issues, comentários ou PRs apenas porque uma skill possui essa etapa; siga o escopo autorizado.

### Triage labels

Vocabulário de referência em `docs/agents/triage-labels.md`. Criar ou alterar labels remotas exige uma tarefa de triagem solicitada.

### Domain docs

Contexto único: `GLOSSARY.md` e decisões em `docs/adr/`. Veja `docs/agents/domain.md`.

## Validação e empacotamento

- Verificações de código: `python -m unittest discover -s tests` e `python scripts/VALIDAR_DEPENDENCIAS_BUILD.py` quando pertinentes à mudança.
- Pacote Windows: `JARVIS.spec` e `.github/workflows/windows-build.yml`.
- O ramo `codex/windows-20261020` dispara a compilação ao receber um push. Atualize-o somente quando uma compilação estiver autorizada.
- Skills e documentação de engenharia são ferramentas de desenvolvimento, não dependências de runtime do JARVIS.
