# Estado real da implementação — 17/10/2026

## Implementado nos fontes

- Esfera volumétrica calculada por shader OpenGL 3.3, sem clipe como padrão.
- Campo de densidade de fumaça, emissão de brasa, turbulência e interpolação de parâmetros por estado/nível de áudio.
- Worker de renderização separado; caixa de entrada de um quadro para não acumular imagens na UI.
- Integração com o nível de áudio já usado pelo HUD. Não abre outro microfone.
- Painel nativo com clima, relógio/calendário, CPU/RAM, comandos pessoais e configuração de casa inteligente.
- Arrastar/redimensionar módulos, escolher visibilidade/cor/opacidade/qualidade e salvar preferências.
- Consulta de cidade e clima via Open-Meteo em threads com timeout, sem cidade ou condição inventada.
- F8 e botão no menu abrem o painel. Transição de SLEEPING para LISTENING abre overlay se outro app estiver ativo; SLEEPING recolhe.

## Verificado nesta máquina

- Shader compilado e quadros renderizados em OpenGL/EGL.
- Prévia animada de seis segundos gerada do shader: estados de espera/escuta/resposta com amplitude controlada. Não é prova de reação a microfone real nem de FPS no Windows.
- Painel Qt offscreen criado; persistência e ciclo mostrar/recolher verificados.

## Pendências e limites

- Qualidade artística ainda em refinamento: mais filamentos delicados e menos granulação para aproximar a fumaça da referência.
- Não aprovado como visual final ou produto comercial concluído.
- Teste completo no Windows com áudio real, hotword, drivers e vários monitores pendente.
- A ponte Qt/GPU entregou quadros no teste offscreen, mas o teste de cadência não atingiu a meta; fluidez não está validada.
- Clima desenhado com gradientes e camadas animadas; não representa simulação física volumétrica de nuvens. Refinamento visual pendente.
- Música e atalhos gerais ainda não possuem cartões dedicados novos.
- Cartão de casa inteligente abre configuração existente; ainda não exibe dispositivos/estados confirmados. Não simula integração.
- Comandos pessoais são pedidos ao motor existente; não são agendamentos nem confirmação de execução.
- O serviço Open-Meteo deve ter plano/termos adequados ao uso comercial antes da distribuição.
- Exige instalação de `moderngl` e driver OpenGL 3.3. Falha de GPU usa compatibilidade com indicação explícita.
- Nenhum EXE ou instalador produzido.

## Testar sem compilar EXE

Instalar dependências Python com `python -m pip install -r requirements.txt` e executar `INICIAR_JARVIS.bat`.
Abrir o painel pelo menu ou F8. Escolher a cidade em Atmosfera. Usar Organizar para mover/redimensionar módulos.
Configurações pessoais, credenciais e vídeos de referência não são publicados no repositório.
