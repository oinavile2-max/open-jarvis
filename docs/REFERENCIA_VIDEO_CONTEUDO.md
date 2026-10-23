# Central editorial inspirada no vídeo do usuário

Referência recebida em 23/10/2026: `jjjoaosales_1792760213_4014283658655302595_27661081223.mp4`, duração aproximada de 2 minutos.

## Elementos observados

- Interface preta com acentos ciano, reator circular J.A.R.V.I.S. e comunicação lateral.
- Relógio, clima e agenda ao lado da interação.
- Pedido para organizar uma semana de conteúdo, criando ideias e roteiros completos.
- Quadro Trello com listas de segunda-feira a domingo; cada cartão contém o conteúdo detalhado.

Os números de seguidores e a conta mostrados no vídeo pertencem à referência e não foram usados como dados do usuário. A implementação é própria: não houve acesso ao código ou à conta do autor.

## Implementação no JARVIS Windows

Acesso: **Central de conteúdo** nos controles do desktop ou **Menu rápido → Atalhos → Central de conteúdo**.

- **Central**: reator nativo em ciano com movimento e estado/amplitude do HUD existente; relógio local; comunicação e atalhos de microfone, interrupção, clima e ajustes.
- **Semana**: sete colunas, seleção de planos, briefing e cartões persistidos em SQLite.
- **Nova semana**: calendário vazio com título, briefing e data da segunda-feira.
- **Planejar com IA**: envia o briefing ao cérebro configurado, pedindo conteúdos originais com gancho, roteiro e CTA; a ferramenta `content_planner` salva o resultado. Uma solicitação à IA não é tratada como plano salvo antes do retorno da ferramenta.
- **Abrir roteiro**: edição local de título, canal, etapa de produção, gancho, roteiro e CTA. Revisão otimista impede salvar sobre uma edição concorrente.
- **Exportar roteiros**: arquivo Markdown escolhido pelo usuário; a ferramenta também pode exportar para `exports/content/`.
- **Enviar novos ao Trello**: cria um quadro privado por plano quando não há ID configurado, ou usa o quadro escolhido. Cria listas por dia/data e cartões com roteiro completo. Preserva cartões pelo ID remoto salvo, mesmo quando a descrição é editada no Trello; marcadores auxiliam a recuperação quando uma resposta se perde. Não sobrescreve edições feitas diretamente no Trello.

Etapas: ideia, roteiro, gravado, editado, agendado e publicado. São estados editoriais definidos pelo usuário: não representam postagem automática em redes sociais.

## Configuração

**Ajustes → Conteúdo / Trello**: chave API, token e ID/código opcional do quadro. O token precisa de acesso de leitura/escrita aos quadros. As credenciais ficam na configuração local existente; não são incluídas nos commits, exports ou pacote.

Documentação oficial consultada:

- https://developer.atlassian.com/cloud/trello/guides/rest-api/authorization/
- https://developer.atlassian.com/cloud/trello/rest/api-group-boards/
- https://developer.atlassian.com/cloud/trello/rest/api-group-lists/
- https://developer.atlassian.com/cloud/trello/rest/api-group-cards/

As requisições usam `Authorization: OAuth ...` em vez de credenciais na URL. Erros de transporte são sanitizados. O envio roda fora da interface, usa tempos limites e uma trava por plano. O botão Cancelar envio e o encerramento do aplicativo sinalizam cancelamento entre requisições; uma requisição já em andamento pode terminar antes de parar. Um envio incompleto pode ter criado parte dos itens; uma nova tentativa consulta o quadro antes de criar mais cartões.

No modo Claude, autorize `content_planner` em **Claude / MCP** para planejar localmente. Instalações sem lista de permissões personalizada recebem essa função no padrão. Listas já configuradas são preservadas e precisam ser alteradas pelo usuário.

`trello_content` tem permissão separada e não é liberada por padrão. Chamadas por voz ou texto também passam pela confirmação visual do HUD; o parâmetro escrito pelo modelo não autoriza o envio sozinho. O botão do quadro pede confirmação antes de escrever na conta configurada.

A configuração do cérebro/voz continua sendo a mesma do projeto: Claude Code autenticado, Gemini para transcrição e Fish Audio para a saída vinculada à sessão conectada. Os novos arquivos não alteram o caminho do microfone ou o algoritmo de interrupção.

## Limites e validação

- O quadro local funciona sem Trello; a criação com IA exige o cérebro conectado e a ferramenta autorizada.
- O relógio usa a hora do Windows. Clima acessa o painel já existente e sua localização configurada.
- As métricas mostradas são totais reais do quadro local. Não há nova conexão Instagram nem reprodução dos números do vídeo.
- A integração implementa a API Trello real, mas nenhuma conta Trello do usuário foi conectada ou alterada durante o desenvolvimento. Testes de protocolo usam transporte de teste explicitamente restrito aos testes.
- Verificados: persistência, datas da semana, rollback, concorrência de edição, confirmação, envio repetido, recuperação após timeout e não exposição de tokens em erros.
- Os planos salvos pela IA são abertos na interface por sinal Qt com o ID do plano, sem depender apenas do título. Comandos à IA são despachados fora da thread da interface.
- O painel e o editor foram abertos e renderizados com PyQt6, usando dados de demonstração em banco temporário. Isso não valida a conta Claude, o áudio real, o Trello real ou uma nova compilação Windows.
- Esta alteração é de código-fonte e não atualiza o EXE anterior.
