# JARVIS: Claude Code e servidor MCP integrado

Ajustes → **Claude / MCP** controla o cérebro principal. O padrão é `claude_code`.
O modo anterior continua disponível selecionando `gemini` e reiniciando.
Esta alteração é de código-fonte; o EXE distribuído anteriormente não contém esta integração.

## Ativação no Windows

1. Instale o Claude Code **nativo** seguindo https://code.claude.com/docs/en/setup.
2. No terminal, execute `claude auth login` e confira `claude auth status`.
3. Nos ajustes, selecione `claude_code`, o executável `claude` (ou caminho completo para `claude.exe`) e o modelo/alias `sonnet`.
4. Em IA, mantenha a chave Gemini para transcrever o microfone. Em Voz, configure Fish Audio e sua chave.
5. Salve e reinicie o JARVIS. Instalações por fonte precisam atualizar `requirements.txt`.

Este modo usa as credenciais do Claude Code, não o campo de chave Anthropic do especialista antigo. O acesso depende do plano e das permissões da conta. Variáveis `ANTHROPIC_*` não são herdadas pelo processo, evitando troca acidental para cobrança API.
Sem CLI/login, o HUD mostra o erro; não troca silenciosamente para outro cérebro.
Sem Fish Audio ativo, a resposta aparece em texto. Sem Gemini, o comando digitado pode funcionar, mas o microfone não terá transcrição. Reconhecimento de rosto permanece local.

## Fluxo

- Texto digitado e comandos do dashboard → Claude.
- Microfone → transcrição Gemini → Claude. A saída de áudio, os textos de resposta e chamadas de ferramenta do Gemini são descartados neste modo.
- Claude → ferramentas MCP autorizadas → dispatcher real do JARVIS → histórico de tarefas.
- Resposta Claude em streaming → frases completas → Fish Audio → fila de áudio existente.
- Interrupção cancela a tarefa do Claude, encerra seu processo e descarta áudio pendente. A próxima mensagem retoma a sessão quando houver ID disponível.

O processo Claude permanece aberto entre turnos para evitar inicialização repetida. `sonnet` é configurável. A transcrição usa o sinal `finished` quando disponível; há fallback para `generation_complete`/`turn_complete`. Não há medição de latência com hardware e contas reais nesta implementação.

## Servidor MCP local

Inicializa no modo Claude e escuta apenas em `127.0.0.1`, em porta livre escolhida pelo sistema. Usa Streamable HTTP, proteção de Host/Origin do FastMCP e token Bearer aleatório por execução. O arquivo de conexão fica em uma pasta temporária privativa, removida ao encerrar normalmente; não é incluído no repositório nem no pacote.

Ferramentas MCP:

- `jarvis_list_tools`: lista somente as funções JARVIS autorizadas, com parâmetros.
- `jarvis_execute(name, arguments)`: valida a autorização e chama o dispatcher existente. Mantém os limites e o histórico de tarefas.

Por padrão, apenas `system_status`, `recall_memory` e `web_search` são autorizadas. O campo **Funções JARVIS autorizadas** aceita nomes separados por vírgula. Adicionar uma função é uma autorização explícita para o Claude executá-la. Funções de automação continuam com suas confirmações internas. Cancelar uma chamada não desfaz efeitos externos já iniciados. `claude_reasoning` é bloqueado para evitar recursão.

As ferramentas nativas de shell/arquivos do Claude estão desabilitadas (`--tools ""`). Não há bypass global de permissões. O processo usa um diretório temporário e `--setting-sources ""`/`--strict-mcp-config`; não importa automaticamente o MCP de outros projetos.

## Outros servidores MCP

https://mcpservers.org/pt-BR/ é um catálogo, não um servidor único. Nenhum servidor do catálogo é instalado automaticamente.

O campo JSON contém um mapa de nomes para configurações, **sem** o invólucro `mcpServers`. Exemplo de formato, substituindo os valores pelo servidor escolhido:

```json
{
  "documentos": {
    "type": "http",
    "url": "https://servidor-exemplo.invalid/mcp"
  }
}
```

Também aceita `stdio` com `command`, `args` e `env`, ou `sse` com `url`. Cadastrar um servidor stdio autoriza iniciar esse comando no computador; ele pode precisar de Node, Python ou credenciais próprios. Não inclua segredos em commits.

O campo **Ferramentas MCP autorizadas** deve conter nomes exatos, como `mcp__documentos__buscar`, separados por vírgulas. Só aceita ferramentas de servidores cadastrados; sem curingas. Ferramentas não liberadas serão bloqueadas no modo sem interação e o HUD informará a necessidade de autorização. O catálogo não concede acesso a GitHub, e-mail ou outros serviços: cada servidor precisa de autenticação própria.

## Validação

`python -m unittest discover -s tests` cobre streaming, processo persistente, cancelamento, permissões e roteamento de transcrição. Com o SDK instalado, faz também handshake MCP real por loopback, listagem, execução autorizada e rejeição de token ausente/função não liberada.

Login real do Claude, voz Fish, microfone e latência completa exigem validação no Windows do usuário. A integração foi inspirada na arquitetura de https://github.com/adewaskar/jarvis; o código é próprio e preserva a interface nativa atual.
