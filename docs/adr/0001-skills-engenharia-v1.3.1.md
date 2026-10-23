# Skills de engenharia fixadas em v1.3.1

Data: 2026-10-23
Estado: adotado por solicitação do usuário.

## Contexto

O usuário pediu que o pacote Matt Pocock Skills fosse replicado no projeto, além de usado pontualmente na revisão anterior.

## Decisão

Incluir as 27 skills estáveis listadas no manifesto do plugin oficial v1.3.1, mantendo seus arquivos originais e licença MIT. Copiar para `.agents/skills/` e `.claude/skills/`, com índice e configuração de domínio no repositório. A duplicação física mantém compatibilidade com Windows sem depender de links simbólicos. Registrar SHA-256 dos arquivos para verificar as duas árvores.

## Consequências

As sessões de desenvolvimento podem descobrir as skills por projeto. Atualizações passam por alteração explícita de versão e integridade. O pacote orienta o desenvolvimento e não é carregado automaticamente como ferramenta do JARVIS em execução. A integração altera arquivos de engenharia e não exige recompilar o aplicativo.
