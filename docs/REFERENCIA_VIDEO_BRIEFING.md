# Central de briefing — segunda referência em vídeo

Referência enviada: `jjjoaosales_1792594805_4012898980530000403_27661081223.mp4` (121,67 segundos). Inspeção visual: foto durante interação, anéis segmentados cianos, cartão central em vidro escuro, faixa horizontal de cartões de notícias, clima, resumos e estado de fala. A análise visual não é uma transcrição do áudio.

## Implementado

- Menu rápido → Atalhos → **Central de briefing · notícias**, e botão **Central de briefing** nos controles do desktop.
- Janela nativa com anéis animados, cartão selecionado, miniaturas horizontais, navegação anterior/próximo e abertura explícita da fonte. Nenhuma rotação automática interrompe a leitura.
- Resultados reais do fluxo `web_search` alimentam a central quando aberta. A última resposta visual é reapresentada ao abrir a central. Fora dela, os cartões de pesquisa também usam o novo carrossel.
- Imagem do artigo quando fornecida pelo buscador de notícias. Apenas a imagem selecionada é carregada, sem bloquear a thread Qt; seleção troca imediatamente. Limite de 4 MiB por imagem, 16 milhões de pixels, limite total de sete segundos (incluindo resolução do host), cache limitado a doze imagens e sem seguir redirecionamentos. Endereços locais/privados são rejeitados na resolução antes da requisição automática. Fonte sem imagem continua utilizável com texto.
- Parser aceita tanto `Source:` / `Fonte:` quanto URLs isoladas do formato antigo de notícias.
- Estado da conversa e amplitude vêm do HUD existente. Animações e relógio param quando o painel fica oculto; download pendente é cancelado ao ocultar ou selecionar outro cartão.
- Foto e nome reutilizam o perfil existente durante a interação; em espera a identificação desaparece. “Foto cadastrada” não significa reconhecimento. “Rosto reconhecido” depende do resultado com prazo de validade já emitido pelo reconhecimento local; não autentica o Windows.
- Atalhos para notícias, tecnologia e resumo do dia enviam pedidos ao motor já configurado em uma thread separada. Clima, perfil e ajustes abrem os módulos reais existentes.

## Limites e validação

Não foram copiados usuário, foto, indicadores, manchetes ou contas do vídeo. Nenhuma notícia de teste é distribuída como dado real. O resumo do dia depende das integrações e permissões disponíveis; não gera compromissos fictícios. O clima usa o painel e a cidade já configurados. Imagem de artigo não é download ou reprodução do vídeo da matéria.

Testes locais cobrem parsing e seleção, limpeza de fonte antiga, estado de perfil e imagens via servidor local. Validação visual feita por captura Qt offscreen. APIs externas, câmera, microfone e conta Claude não foram validados ao vivo nesta alteração. Não foi executada compilação Windows nem gerado EXE.
