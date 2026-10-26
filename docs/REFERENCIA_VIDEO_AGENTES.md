# Central de agentes — ChilenoAPPs

Referência: `kaiogomes.g_1792876631_4014620551644094898_38202006624.mp4`, 125,15 segundos. A inspeção visual mostra uma assistente paralela ao JARVIS, tarefas atribuídas ao Claude Code e Cursor, programação/documentação, progresso individual e o resultado de um jogo de cobrinha. Não é uma transcrição completa do áudio.

## Implementação

Acesso: **Menu rápido → Atalhos → Central de agentes · programação**. A conversa pode preparar o objetivo com a ferramenta `agent_workspace`; isso só abre a central. O usuário edita o plano e clica **Iniciar agentes** para iniciar inferência.

Há um modelo inicial com programador, documentador e revisor. Programador e documentador trabalham em paralelo; o revisor recebe ambos os resultados após a conclusão. Os agentes, instruções, modelos Claude (sonnet/haiku/opus), arquivos de responsabilidade, dependências e objetivo são editáveis. Limites: oito tarefas por execução, até três processos simultâneos, três minutos por agente e 1 MiB de arquivos de texto por agente. O estado, contagem de caracteres e duração são observados, sem percentuais ou tokens inventados.

O Claude Code nativo usa o login já configurado em **Ajustes → Claude / MCP**. Cada tarefa usa processo próprio e saída estruturada JSON; o JARVIS valida os arquivos e os salva. Ferramentas de shell, acesso direto a arquivos e servidores MCP estão desabilitados nesses processos. Eles recebem o objetivo e os resultados das dependências, sem envio de arquivos de projetos ou da memória pessoal do JARVIS. Não há execução automática do código produzido, instalação de pacotes, publicação ou build.

Escolha uma pasta de saída. Cada execução cria `jarvis-agentes-<id>/agentes/<agente>/` e preserva os artefatos concluídos mesmo se outra tarefa falhar. Somente quando todos entregam os arquivos, o JARVIS monta `projeto/` com as entregas combinadas. A ação **Abrir arquivos** abre a pasta; não executa o HTML ou scripts. Projetos existentes não são sobrescritos. Caminhos absolutos, travessia de diretórios, nomes reservados do Windows e disputas de arquivos são rejeitados. Entregas incompletas ou fora da responsabilidade falham sem promover arquivos parciais.

O histórico SQLite permanece em `config/agent_runs.sqlite3`, local e excluído dos pacotes. A janela pode ser recolhida enquanto os agentes trabalham. **Cancelar execução** encerra os processos; fechar o aplicativo também cancela. Sessões anteriores incompletas são exibidas como interrompidas e não reiniciam sozinhas. Concluído significa **arquivos entregues**, não código testado nem revisão aprovada.

## Matriz cumulativa de preservação

| Área acordada | Tratamento nesta alteração | Verificação |
|---|---|---|
| Voz, microfone e interrupção natural | Fluxo de áudio não alterado; agentes em thread/event loop próprios | Testes existentes de áudio e cancelamento |
| Esferas, perfil e Face ID | Renderização e identidade preservadas | Testes existentes de briefing/perfil |
| Cards e notícias com fontes | Carrossel anterior preservado | Testes existentes de cards/imagens |
| Quadro editorial e Trello | Mantidos e separados dos agentes | Testes existentes de planejamento/Trello |
| Claude como cérebro e MCP | Mantidos; nova ferramenta somente prepara a central | Testes existentes de permissões/protocolo |
| Agentes de programação/documentação/revisão | Novo painel, dependências e paralelismo limitados | Testes do agendador, CLI, histórico e UI |
| Builds somente mediante pedido | Nenhuma compilação Windows executada | Apenas código-fonte atualizado |
| Créditos | Novo módulo e UI atribuídos a ChilenoAPPs | Inspeção de código/documentação |

## Limites e pendências

- Cursor aparece no vídeo; sua integração não foi implementada. Todos os agentes desta versão executam no Claude Code; nenhum agente Cursor é simulado.
- A central gera arquivos de texto novos. Não lê nem altera projetos existentes, não executa testes dos projetos gerados e não gera EXE/APK.
- O paralelismo pode consumir limites do plano Claude. Sem instalação/login válido há erro, sem resultado fictício.
- Testes usam executores controlados e subprocessos Python locais; não houve validação paga com conta Claude nem teste do EXE Windows.
- Os demais requisitos históricos do JARVIS não são declarados completos por esta alteração; esta matriz registra preservação, não substitui validação de hardware e serviços reais.

Base técnica do CLI: [documentação oficial do Claude Code](https://code.claude.com/docs/en/cli-reference), especialmente saída estruturada, restrição de ferramentas e configuração MCP explícita.
