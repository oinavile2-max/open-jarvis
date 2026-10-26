"""Prepare the native agent planner; launching paid inference remains a UI action."""
import json


def agent_workspace(parameters=None,player=None,**kwargs):
    brief=str((parameters or {}).get('brief') or '').strip()
    if len(brief)>12000:return json.dumps({'error':'Objetivo excede 12000 caracteres.'},ensure_ascii=False)
    if not player or not hasattr(player,'show_agent_workspace'):
        return json.dumps({'error':'A central de agentes requer a interface desktop.'},ensure_ascii=False)
    player.show_agent_workspace(brief)
    return json.dumps({'status':'prepared','message':'Objetivo enviado à central. O usuário revisa os agentes e clica Iniciar agentes. Nenhum agente foi executado ainda.'},ensure_ascii=False)


TOOL={'name':'agent_workspace','description':'Abre a central de agentes para preparar programação, documentação e revisão em paralelo. Não inicia execução: o usuário revisa e inicia pela interface.',
      'parameters':{'type':'OBJECT','properties':{'brief':{'type':'STRING','description':'Objetivo completo do projeto a delegar aos agentes.'}},'required':['brief']},'handler':agent_workspace}
