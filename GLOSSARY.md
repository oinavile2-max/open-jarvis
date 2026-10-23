# Vocabulário do JARVIS OS Windows

| Termo | Significado neste projeto |
|---|---|
| Cérebro | Provedor responsável por interpretar pedidos e produzir respostas; configurável entre Claude Code e o modo Gemini existente. |
| Claude Code | Executável nativo autenticado pelo usuário, usado como processo persistente no modo Claude. |
| Camada de transcrição | Gemini Live recebendo áudio do microfone e fornecendo texto no modo Claude; suas respostas e ferramentas são descartadas nesse modo. |
| Fish Audio | Serviço de síntese de voz. Nesta versão sua saída usa o ciclo da sessão Gemini conectada. |
| Servidor MCP local | Interface autenticada em loopback que expõe apenas as funções JARVIS autorizadas. |
| Ferramenta | Função executável com parâmetros e resultado verificável; sua disponibilidade não garante autorização. |
| Interrupção | Cancelamento da resposta e descarte do áudio pendente para aceitar uma correção do usuário. |
| Esfera | Elemento visual reativo ao estado e ao áudio, com estilos selecionáveis no menu rápido. |
| Perfil com foto | Foto e nome cadastrados para exibição durante interação; cadastro não significa reconhecimento facial. |
| Correspondência facial local | Comparação visual local de rosto; não equivale a Windows Hello ou autenticação do sistema. |
| Smoke test do pacote | Verificação executada pelo EXE compilado para importações, interface, recursos e protocolo MCP; não valida contas externas nem hardware real. |
| Skill de engenharia | Instrução de trabalho para o agente que desenvolve o projeto, distinta de uma ferramenta MCP do JARVIS. |
| Plano editorial | Semana iniciada na segunda-feira, com briefing e cartões de conteúdo persistidos localmente. |
| Cartão de conteúdo | Ideia com canal, data editorial, gancho, roteiro, CTA e etapa de produção; publicação social é uma ação diferente. |
| Publicação no Trello | Envio explícito de novos cartões ao quadro da conta configurada; não significa publicação em uma rede social. |
