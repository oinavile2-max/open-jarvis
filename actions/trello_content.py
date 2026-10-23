"""Separate external-write permission from local editorial planning."""
import json
from core.content_planner import default_planner
from core.trello_content import TrelloError, publish_plan, trello_config


def trello_content(parameters=None, **kwargs):
    p=parameters or {}
    try:
        if p.get('confirmed') is not True:
            raise ValueError('Peça autorização explícita antes de enviar ao Trello.')
        planner=default_planner()
        plan=planner.get_plan(p.get('plan_id',''))
        from core import confirm
        def run():
            result=publish_plan(planner,plan['id'],trello_config(),confirmed=True)
            return json.dumps(result,ensure_ascii=False)
        return confirm.request('trello:'+plan['id'],'Enviar plano ao Trello',
            f"Enviar {len(plan['cards'])} cartões de {plan['title']} à conta configurada? Se não houver quadro definido, será criado um quadro privado.",run)
    except (TrelloError,ValueError) as exc:
        return json.dumps({'error':True,'message':str(exc)},ensure_ascii=False)


TOOL={'name':'trello_content','description':
      'Envia os NOVOS cartões de um plano local ao Trello configurado, em listas por dia da semana. '
      'Se nenhum quadro estiver configurado, cria um quadro privado para esse plano. '
      'Use somente quando o usuário pedir explicitamente envio ao Trello e confirmed=true. '
      'É uma escrita externa, exige token/chave com permissão. Preserva cartões já existentes e reconcilia tentativas anteriores. '
      'Não publica em Instagram, TikTok ou YouTube.',
      'parameters':{'type':'OBJECT','properties':{'plan_id':{'type':'STRING'},'confirmed':{'type':'BOOLEAN'}},
                    'required':['plan_id','confirmed']},'handler':trello_content}
