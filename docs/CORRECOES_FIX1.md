# Correções após teste no PC

Sintomas relatados: microfone conectado após iniciar não aparece, esfera no modo de compatibilidade se afasta da referência de fogo, ausência de acesso visível aos ajustes e parada durante a resposta.

## Alterações

- Captura/renderização: monitor Windows lê a presença dos endpoints Capture/Render sem depender do cache do PortAudio. Uma mudança estável solicita reconexão; somente após fechar as streams a enumeração nativa é reinicializada. A seleção salva por nome é reaplicada. O seletor atualiza a lista em segundo plano.
- Reprodução: substituído Pa_WriteStream bloqueante por callback com fila e espera limitada. Se o dispositivo parar de consumir áudio, uma falha explícita provoca reconexão. A causa específica do travamento relatado ainda depende dos logs do PC.
- Interface: janela de controles independente do wallpaper click-through, com Ajustes e Áudio/microfone. O painel de ajustes oferece acesso aos logs.
- Visual: fallback volumétrico procedural por CPU em lugar dos fios do render antigo. GPU continua preferida. O fallback tem resolução e frequência limitadas e não equivale à qualidade premium por GPU.
- Diagnóstico: watchdog do event loop registra stacks quando Qt deixa de responder por mais de 5 segundos.

## Verificação

Testes de troca estável de endpoints, reenumeração, preservação PCM, preenchimento com silêncio, timeout de saída, desbloqueio ao desconectar, volume CPU reativo e alpha pré-multiplicado. Hardware real, conexão com API e fidelidade visual em movimento ainda precisam ser verificados no PC afetado.
