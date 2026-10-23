"""Editorial calendar tool; AI supplies the ideas and complete scripts."""
import json
from datetime import date,timedelta
from core.content_planner import default_planner, plan_markdown, project_root


def content_planner(parameters=None, player=None, **kwargs):
    p = parameters or {}
    planner = default_planner()
    try:
        operation = p.get('operation', 'list')
        if operation == 'list':
            today=date.today()
            result = {'today':today.isoformat(),'this_week_monday':(today-timedelta(days=today.weekday())).isoformat(),'plans': planner.list_plans()}
        elif operation == 'create':
            key = planner.create_plan(p.get('title', ''), p.get('week_start', ''), p.get('brief', ''), p.get('cards', []))
            saved = planner.get_plan(key)
            if player is not None and hasattr(player,'show_content_plan'):
                try:player.show_content_plan(key)
                except RuntimeError:pass
            result = {'id':key,'title':saved['title'],'week_start':saved['week_start'],'total':len(saved['cards'])}
        elif operation == 'read': result = planner.get_plan(p.get('plan_id', ''))
        elif operation == 'add':
            result = {'card_id': planner.add_card(p.get('plan_id', ''), p.get('card', {}))}
        elif operation == 'update':
            planner.update_card(p.get('card_id', ''), p.get('changes', {}), expected_revision=p.get('revision'))
            result = {'saved': True}
        elif operation == 'export':
            plan = planner.get_plan(p.get('plan_id', ''))
            directory = project_root()/'exports'/'content'; directory.mkdir(parents=True, exist_ok=True)
            path = directory/(plan['id']+'.md')
            path.write_text(plan_markdown(plan), encoding='utf-8')
            result = {'path': str(path), 'saved': True}
        else: raise ValueError('Operação desconhecida.')
        return json.dumps(result, ensure_ascii=False)
    except (ValueError, OSError) as exc:
        return json.dumps({'error': True, 'message': str(exc)}, ensure_ascii=False)


CARD = {'type': 'OBJECT', 'properties': {
    'day': {'type': 'INTEGER', 'description': '0=segunda, 6=domingo'},
    **{key: {'type': 'STRING'} for key in ('title','channel','hook','script','cta','status')}}, 'required': ['day','title']}
TOOL = {'name': 'content_planner', 'description':
    'Planeja a semana editorial do usuário em um quadro local de segunda a domingo. '
    'Para criar, primeiro elabore ideias originais a partir do briefing do usuário e forneça gancho, roteiro completo e CTA em cada cartão. '
    'Não copie os textos do vídeo de referência. Até 70 cartões por plano. week_start é a segunda-feira AAAA-MM-DD. '
    'list/read consultam planos; create/add/update gravam localmente; export salva Markdown. '
    'Um cartão agendado indica planejamento editorial, não publicação automática em rede social.',
    'parameters': {'type':'OBJECT', 'properties': {
        'operation': {'type':'STRING','enum':['list','create','read','add','update','export']},
        **{key:{'type':'STRING'} for key in ('plan_id','card_id','title','week_start','brief')},
        'cards': {'type':'ARRAY','items':CARD}, 'card':CARD,
        'changes': {'type':'OBJECT','properties':{key:{'type':'STRING'} for key in ('title','channel','hook','script','cta','status')}},
        'revision': {'type':'INTEGER'}}, 'required':['operation']}, 'handler':content_planner}
