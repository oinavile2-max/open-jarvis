# Refinamento da esfera

A referência videoplayback.mp4 orienta apenas as ramificações neuronais, sem reproduzir o formato do cérebro nem incorporar o vídeo.

- Novas fibras curvas e afiladas com bifurcações e impulsos propagados. Composição procedural no pós-processamento, com profundidade estilizada; não simula neurônios biológicos.
- Ativação gradual em THINKING/PROCESSING; desativação ao silenciar e nos demais estados.
- Removido o jitter espacial que produzia granulação. Mais amostras na integração volumétrica: 48/80/112 nos perfis economy/balanced/premium.
- Menor densidade de fundo e menor emissão para preservar filamentos prateados, sombras e detalhes internos da brasa.

Verificados compilação GLSL e frames dos quatro estados nos três perfis, alpha pré-multiplicado e sintaxe Python. Inspeção de frame em qualidade premium realizada.

Ainda falta avaliar fluidez e custo na GPU Windows do usuário e comparar o movimento completo com a referência. Os níveis de FPS configurados são metas, não medições de desempenho. Sem EXE gerado.
