# Controle de fala e tarefas — Windows

Implementação própria, inspirada na organização descrita em https://github.com/ethanplusai/jarvis.
Nenhum arquivo de implementação desse repositório foi incorporado.

- `core/speech_controller.py`: cancelamento único do PCM; geração invalida escrita atrasada após interrupção.
- `core/audio_output.py`: descarta fila sem reabrir dispositivo; áudio já no buffer físico depende do driver.
- `core/task_runs.py`: histórico SQLite em config/task_runs.sqlite3, estados finais, recuperação de tarefas abandonadas.
- `core/task_history_widget.py`: Menu rápido > Tarefas; consulta fora da thread Qt, sem armazenar argumentos ou conteúdo das respostas.
- `core/preflight.py`: diagnóstico de áudio e presença de chave; roda em paralelo à conexão. Não valida a chave na rede.
- `ui.py`: memória existente ganhou edição, mantém exclusão e informa uso pela IA.
- `main.py`: preferência de respostas curtas, limite de 60 s por chamada de ferramenta, sem gerar outro turno só para narrar erro.

Limites: tempo esgotado/cancelamento para de esperar, mas não mata funções já rodando em threads nem desfaz ações externas. A interface informa essa condição. Não há percentual artificial de progresso. Face ID, novo visual dos cards e redução do pacote executável não fazem parte desta alteração.

Validação automática local; sem prova de áudio real/GUI no Windows. Sem ZIP, build ou EXE.
