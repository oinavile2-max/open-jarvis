# Fluxo de voz Android V19 → Windows

Comparação realizada com JARVIS_OS_ANDROID_LIVE_V19_SEM_BUILD.zip, AudioRecorder.kt e GeminiLiveWebSocket.kt.

## Alterações aplicadas

- main.py: captura PCM16 mono a 16 kHz em blocos de 320 amostras (640 bytes / 20 ms), como no Android.
- Fila de envio limitada a 10 blocos (200 ms de PCM aguardando envio, sem contar a transmissão em andamento). Antes eram 64 blocos de 32 ms, aproximadamente 2,05 segundos.
- Solicitação de latência baixa ao PortAudio para entrada e saída. O valor efetivo depende do driver; o código continua medindo a latência da saída.
- Mantidos envio contínuo, fechamento local de turno, reprodução progressiva e configuração existente de raciocínio desativado por padrão.

## Limites da adaptação

O Android usa VOICE_COMMUNICATION com cancelamento de eco, supressão de ruído e ganho fornecidos pelo dispositivo. Esses efeitos não foram copiados para o Windows como se fossem equivalentes ao EchoGuard existente.

Reduzir a fila evita acumular áudio antigo sob congestionamento, mas pode descartar mais quadros quando a conexão não acompanha. Não representa garantia de menor tempo total de resposta da API.

## Verificação

Três testes existentes de ordenação PCM/fim de turno e descarte sob congestionamento passaram. Sintaxe Python e git diff --check passaram.

Pendente: medir no PC Windows com microfone e alto-falantes reais; observar cortes na fala, estalos e tempo entre fim da fala, primeiro áudio recebido e reprodução. Sem medição ao vivo nem EXE gerado.
