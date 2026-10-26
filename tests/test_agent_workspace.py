import asyncio
import tempfile
from pathlib import Path
import sys
import unittest
from core.agent_workspace import AgentTask,AgentWorkspace,AgentRuns,ClaudeArtifactAgent,validate_tasks

class ValidationTests(unittest.TestCase):
    def test_paths_conflicts_and_cycles(self):
        for path in ['../a','/etc/a','C:/x','A\\b','a/../b','NUL.txt','x.']:
            with self.assertRaises(ValueError):validate_tasks([AgentTask('a','A','T',(path,))])
        for tasks in [
            [AgentTask('a','A','T',('X.txt',)),AgentTask('b','B','T',('x.TXT',))],
            [AgentTask('a','A','T',('a',)),AgentTask('b','B','T',('a/b',))],
            [AgentTask('a','A','T',('a',),('b',)),AgentTask('b','B','T',('b',),('a',))]]:
            with self.assertRaises(ValueError):validate_tasks(tasks)
    def test_real_command_disables_tools(self):
        runner=ClaudeArtifactAgent({'claude_command':sys.executable})
        command=runner.command(AgentTask('a','A','T',('a',)))
        self.assertEqual(command[command.index('--tools')+1],'')
        self.assertIn('--strict-mcp-config',command)
        self.assertNotIn('--dangerously-skip-permissions',command)

class SchedulerTests(unittest.IsolatedAsyncioTestCase):
    async def test_parallel_dependencies_and_persistent_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            active=0;maximum=0;calls=[]
            async def runner(task,brief,context,progress):
                nonlocal active,maximum
                active+=1;maximum=max(active,maximum);calls.append((task.id,tuple(context)))
                await asyncio.sleep(.02);active-=1
                return {'summary':'Gerado','files':[{'path':task.files[0],'content':task.id}]}
            store=AgentRuns(Path(tmp)/'runs.sqlite3');engine=AgentWorkspace(store,runner)
            tasks=[AgentTask('a','Código','Criar',('index.html',)),AgentTask('b','Docs','Criar',('README.md',)),AgentTask('c','Revisão','Revisar',('REVIEW.md',),('a','b'))]
            result=await engine.run('Site',tasks,tmp)
            self.assertEqual(result['state'],'succeeded');self.assertEqual(maximum,2)
            self.assertEqual(calls[-1],('c',('a','b')))
            self.assertEqual((Path(result['project'])/'index.html').read_text(),'a')
            self.assertEqual(store.recent()[0]['id'],result['id'])
    async def test_invalid_result_blocks_dependents_without_partial_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            async def runner(*args):return {'summary':'X','files':[{'path':'evil.txt','content':'x'}]}
            engine=AgentWorkspace(AgentRuns(Path(tmp)/'runs.db'),runner)
            result=await engine.run('Site',[AgentTask('a','A','T',('a.txt',)),AgentTask('b','B','T',('b.txt',),('a',))],tmp)
            self.assertEqual(result['tasks']['a']['state'],'failed')
            self.assertEqual(result['tasks']['b']['state'],'blocked')
            self.assertFalse((Path(result['folder'])/'agentes'/'a').exists())
            self.assertNotIn('project',result)
    async def test_cancel_reaps_all_agents_and_persists_terminal_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            started=asyncio.Event();finished=[]
            async def runner(*args):
                started.set()
                try:await asyncio.sleep(20)
                finally:finished.append(True)
            store=AgentRuns(Path(tmp)/'runs.db');engine=AgentWorkspace(store,runner)
            job=asyncio.create_task(engine.run('X',[AgentTask('a','A','T',('a',))],tmp))
            await started.wait();job.cancel();result=await job
            self.assertEqual(result['state'],'cancelled');self.assertEqual(finished,[True])
            self.assertFalse(engine.running);self.assertEqual(store.recent()[0]['state'],'cancelled')
    async def test_timeout_is_failure_not_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            async def runner(*args):await asyncio.sleep(10)
            engine=AgentWorkspace(AgentRuns(Path(tmp)/'runs.db'),runner)
            result=await engine.run('X',[AgentTask('a','A','T',('a',))],tmp,timeout=.01)
            self.assertEqual(result['state'],'failed')

    async def test_cli_protocol_and_cancellation_reaps_native_process(self):
        import json
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            script=Path(tmp)/'agent.py'
            script.write_text('import sys,json,time\np=json.loads(sys.stdin.read())\nif p["objetivo"]=="esperar": time.sleep(30)\nprint(json.dumps({"type":"result","subtype":"success","structured_output":{"summary":"ok","files":[{"path":"a.txt","content":"resultado"}]}}),flush=True)\n')
            runner=ClaudeArtifactAgent({});runner.command=lambda task:[sys.executable,'-u',str(script)]
            task=AgentTask('a','A','T',('a.txt',))
            result=await runner(task,'gerar',{},lambda n:None)
            self.assertEqual(result['files'][0]['content'],'resultado')
            original=asyncio.create_subprocess_exec;captured=[];started=asyncio.Event()
            async def create(*args,**kwargs):
                process=await original(*args,**kwargs);captured.append(process);started.set();return process
            with patch('core.agent_workspace.asyncio.create_subprocess_exec',create):
                pending=asyncio.create_task(runner(task,'esperar',{},lambda n:None))
                await started.wait();await asyncio.sleep(.03);pending.cancel()
                with self.assertRaises(asyncio.CancelledError):await pending
            self.assertIsNotNone(captured[0].returncode)

    async def test_failure_propagates_to_reverse_ordered_descendants(self):
        with tempfile.TemporaryDirectory() as tmp:
            async def runner(*args):raise ValueError('Falhou')
            engine=AgentWorkspace(AgentRuns(Path(tmp)/'runs.db'),runner)
            tasks=[AgentTask('c','C','T',('c',),('b',)),AgentTask('b','B','T',('b',),('a',)),AgentTask('a','A','T',('a',))]
            result=await engine.run('X',tasks,tmp)
            self.assertEqual([r['state'] for r in result['tasks'].values()],['blocked','blocked','failed'])
    async def test_large_context_only_fails_its_dependent(self):
        with tempfile.TemporaryDirectory() as tmp:
            async def runner(task,*args):
                if task.id=='c':await asyncio.sleep(.03)
                return {'summary':'ok','files':[{'path':task.files[0],'content':'x'*300001 if task.id=='a' else 'ok'}]}
            engine=AgentWorkspace(AgentRuns(Path(tmp)/'runs.db'),runner)
            tasks=[AgentTask('a','A','T',('a',)),AgentTask('b','B','T',('b',),('a',)),AgentTask('c','C','T',('c',))]
            result=await engine.run('X',tasks,tmp)
            self.assertEqual([r['state'] for r in result['tasks'].values()],['succeeded','failed','succeeded'])
