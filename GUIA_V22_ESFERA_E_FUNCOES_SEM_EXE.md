# JARVIS Windows V22 — pacote de código-fonte, SEM EXE

**Atualização de 17/10/2026**. Continuidade do código-fonte V22 e da correção de latência anterior.

## Esfera — modo de espera fiel ao vídeo

- A esfera padrão agora usa **os quadros reais do vídeo enviado pelo usuário**, em vez de uma aproximação sintética. O MP4 original foi incluído em `assets/orb/esfera_referencia_usuario.mp4` **sem recodificar a imagem** (apenas removendo a faixa de áudio).
- O vídeo é **mostrado dentro do próprio HUD**, sem navegador, usando QtMultimedia (`QVideoSink`) ou decodificação alternativa via OpenCV em uma thread separada.
- A animação fica em loop, iniciando na fase luminosa e pulando a transição escura inicial. As mudanças de estado modulam suavemente o tamanho, a aura e a velocidade; a amplitude do microfone e da voz sintetizada influencia as reações.
- Se ambos os decodificadores falharem, a animação procedural `LivingOrb` do pacote anterior continua funcionando, com informação de erro.
- `config/ux.json`: `orb_renderer = video_reference` (padrão). Para desabilitar a referência, `procedural`; `orb_quality` controla o detalhamento procedural.
- **Limite de fidelidade**: o modo de espera reutiliza as imagens do vídeo original. As reações em tempo real são novas, inspiradas no vídeo, pois ele não continha uma especificação técnica de reação ao áudio. Um clipe repetido pode apresentar uma transição na volta ao início. É preciso verificar visualmente em um PC com Qt e alto-falante/microfone para aprovar o resultado final.

## Melhorias efetivamente integradas

1. **Latência da conversa**: preserva o aviso explícito de fim de fala para Gemini Live, a fila de entrada com limite e os testes de telemetria/ordem de eventos do pacote anterior.
2. **Volume da voz independente**: controle de **0 a 200%** nas configurações rápidas. Amplificação do PCM com limitador de picos e sem alterar o volume mestre do Windows; persistência em `config/voice_output.json`.
3. **Cards vidro fumê**: cartões de conteúdo com fundo preto translúcido e bordas discretas. Foi removido o fechamento automático de 12 segundos; fecham pelo botão. Ajustes de `showNormal()/raise_()` ajudam a reabrir o card.
4. **Imagem dentro do card**: nova ação `image_viewer` abre PNG, JPG, BMP ou WebP **locais**, sem navegador, dentro do cartão. Imagens remotas requerem uma integração/download validado.
5. **Vídeo dentro do JARVIS**: o player existente é mantido e o modo `video_player` **não abre mais o navegador como fallback involuntário**. Links do YouTube dependem do `yt-dlp`, formatos disponibilizados e conexão: a abertura pode falhar e será comunicada.
6. **Spotify básico**: ação `spotify_control` para abrir o app, procurar música e enviar controles globais de reprodução do Windows. Reproduzir uma faixa específica por conta própria ainda requer API/autorizações Spotify e um dispositivo ativo.
7. **Início automático com Windows**: em primeiro uso, registra a inicialização na chave **HKCU Run** do usuário, por padrão habilitada em `config/startup.json`. Quem desligar pelo botão tem a escolha persistida, sem religar à força.
8. **Pesquisa e personalidade**: as instruções conversacionais passaram a pedir narração natural, explicações, análise separada dos fatos, humor discreto, menos avisos de RAM e respeito ao contexto da família.
9. **Convívio familiar (segurança inicial)**: `core/family_gate.py` define consentimento, horário de silêncio e espaçamento entre intervenções. **Não está conectado à captura ambiental contínua**, que depende de autorização real das pessoas presentes e de integração/validação com STT. Arquivo `config/family_mode.json` mantém o recurso desabilitado por padrão.

## Validação realmente feita

- Testes de lógica automatizados: **16 testes aprovados** (fila/latência, esfera procedural, ganho de voz e política de consentimento).
- Verificação de sintaxe de todo o código-fonte Python: aprovada.
- Quatro amostras decodificadas do vídeo original e do arquivo empacotado, em 2,2 s, 10 s, 39 s e 58,3 s: **quadros idênticos pixel a pixel**.

## Ainda não validado — não declarar comercialmente finalizado

- Execução gráfica real com PyQt6 no Windows, renderização Qt/OpenCV, FPS, memória e GPU: esta máquina de preparação **não tem PyQt6**, e a tentativa de instalar não conseguiu alcançar o repositório de pacotes.
- Escuta/voz/speaker e desempenho Gemini em internet e equipamentos reais.
- Compatibilidade de codecs em cada PC, fluidez da animação, integração completa do modo Família com transcrição consentida e personalidade proativa contextual.
- Reabertura de todos os cards/casos de erro em todas as telas/monitores Windows, permissões de vídeo/Spotify, autonomia avançada e alterações reais do sistema.
- Reprodução automática de qualquer música solicitada no Spotify, sem conta/configuração autorizada: **não está pronta**.
- Autonomia irrestrita do computador: **não implantada**, por exigir políticas de permissão, confirmações e testes rigorosos para operações destrutivas.

## Teste no seu Windows sem criar executável

1. Descompactar este pacote em uma **pasta nova**, preservando o anterior como backup.
2. Com Python instalado e dependências disponíveis, abrir `INICIAR_JARVIS.bat` (inicia o programa; **não gera EXE**).
3. Em configurações rápidas, mover o controle **VOZ JARVIS 0–200%**.
4. Conferir na tela a esfera em espera, ouvindo, pensando e respondendo, e testar desempenho; ao abrir vídeo, a esfera dá lugar ao conteúdo dentro da interface.
5. Abrir um card de texto e confirmar que não some sozinho; solicitar abertura de uma imagem local ou um vídeo.
6. Para testes de lógica sem EXE, executar `TESTAR_CODIGO.bat`.
7. Se a esfera não reproduzir o vídeo, verificar o diagnóstico e as dependências PyQt6/QtMultimedia/OpenCV.

**Distribuição comercial:** verificar direitos de uso do vídeo de referência antes de redistribuí-lo para terceiros. O usuário o forneceu como referência de desenvolvimento, não como comprovação de licença comercial.

**Nenhum EXE, instalador, APK ou compilação final foi gerado neste trabalho.**
