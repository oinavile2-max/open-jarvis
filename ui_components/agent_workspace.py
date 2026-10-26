"""ChilenoAPPs — native agent control room, isolated from the realtime voice loop."""
from __future__ import annotations
import asyncio
import json
from pathlib import Path
import threading
import time

from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,
    QPlainTextEdit,QTreeWidget,QTreeWidgetItem,QComboBox,QSpinBox,QFileDialog,QDialog,
    QFormLayout,QDialogButtonBox,QMessageBox,QSplitter)
from core.agent_workspace import AgentTask,AgentRuns,AgentWorkspace,validate_tasks
from core.content_planner import project_root

STATES={'queued':'Na fila','starting':'Iniciando','running':'Trabalhando','succeeded':'Concluído',
        'interrupted':'Sessão interrompida','failed':'Falhou','blocked':'Bloqueado','cancelled':'Cancelado'}


class TaskEditor(QDialog):
    def __init__(self,task=None,parent=None):
        super().__init__(parent);self.setWindowTitle('Configurar agente');self.resize(600,530)
        task=task or AgentTask('agente','Especialista','',('resultado.md',))
        form=QFormLayout(self)
        self.key=QLineEdit(task.id);form.addRow('ID único',self.key)
        self.role=QLineEdit(task.role);form.addRow('Função',self.role)
        self.model=QComboBox();self.model.addItems(['sonnet','haiku','opus']);self.model.setCurrentText(task.model);form.addRow('Modelo Claude',self.model)
        self.files=QLineEdit(', '.join(task.files));form.addRow('Arquivos · separados por vírgula',self.files)
        self.depends=QLineEdit(', '.join(task.depends));form.addRow('Depende dos IDs · vírgula',self.depends)
        self.prompt=QPlainTextEdit(task.prompt);form.addRow('Instruções completas',self.prompt)
        buttons=QDialogButtonBox();buttons.addButton('Salvar',QDialogButtonBox.ButtonRole.AcceptRole);buttons.addButton('Cancelar',QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);form.addRow(buttons)
    def value(self):
        split=lambda value:tuple(p.strip() for p in value.split(',') if p.strip())
        return AgentTask(self.key.text().strip(),self.role.text().strip(),self.prompt.toPlainText().strip(),split(self.files.text()),split(self.depends.text()),self.model.currentText())


class AgentWindow(QWidget):
    updated=pyqtSignal(object)
    ended=pyqtSignal(str)
    def __init__(self,config_loader=None,parent=None):
        super().__init__(parent,Qt.WindowType.Window)
        self.setWindowTitle('JARVIS · Central de agentes | ChilenoAPPs');self.resize(1230,850);self.setMinimumSize(950,700)
        self.config_loader=config_loader or (lambda:{})
        self.store=AgentRuns(project_root()/'config'/'agent_runs.sqlite3')
        self.tasks=[];self.current=None;self.thread=None;self.loop=None;self.job=None;self.stop=threading.Event()
        self.setStyleSheet('''QWidget{background:#090b17;color:#e6e9fa;font-family:Segoe UI;font-size:12px;}
        QPushButton{background:#191a35;border:1px solid #524172;border-radius:8px;padding:9px 13px;}
        QPushButton:hover{border-color:#cf86da;} QPushButton:disabled{color:#555b70;}
        QLineEdit,QPlainTextEdit,QTreeWidget,QComboBox,QSpinBox{background:#101326;border:1px solid #34334d;border-radius:6px;padding:7px;}
        QTreeWidget::item{height:42px;} QTreeWidget::item:selected{background:#35294b;}''')
        layout=QVBoxLayout(self);layout.setContentsMargins(24,22,24,22);layout.setSpacing(12)
        top=QHBoxLayout();title=QLabel('◈  JARVIS / ORQUESTRAÇÃO DE AGENTES');title.setStyleSheet('color:#d79ce7;font-size:18px;font-weight:600;');top.addWidget(title);top.addStretch()
        hide=QPushButton('Recolher');hide.clicked.connect(self.hide);top.addWidget(hide);layout.addLayout(top)
        note=QLabel('Claude Code precisa estar instalado e autenticado. Cada agente pode consumir limites do seu plano.\nGeração de arquivos de texto; sem executar código, comandos ou instalar dependências. Desenvolvedor: ChilenoAPPs.');note.setWordWrap(True);layout.addWidget(note)
        self.brief=QPlainTextEdit();self.brief.setPlaceholderText('Descreva o projeto e o resultado esperado…');self.brief.setMaximumHeight(95);layout.addWidget(self.brief)
        row=QHBoxLayout();self.add=QPushButton('+ Agente');self.add.clicked.connect(self.add_task);row.addWidget(self.add)
        self.edit=QPushButton('Editar selecionado');self.edit.clicked.connect(self.edit_task);row.addWidget(self.edit)
        self.remove=QPushButton('Remover');self.remove.clicked.connect(self.remove_task);row.addWidget(self.remove)
        self.template=QPushButton('Modelo: projeto web');self.template.clicked.connect(self.load_template);row.addWidget(self.template)
        row.addStretch();row.addWidget(QLabel('Agentes simultâneos'));self.parallel=QSpinBox();self.parallel.setRange(1,3);self.parallel.setValue(2);row.addWidget(self.parallel);layout.addLayout(row)
        split=QSplitter();layout.addWidget(split,1)
        self.tree=QTreeWidget();self.tree.setHeaderLabels(['Agente / modelo','Estado','Depende de','Arquivos','Tempo / saída']);self.tree.setColumnWidth(0,190);self.tree.setColumnWidth(3,180);self.tree.setRootIsDecorated(False);self.tree.setIndentation(0)
        self.tree.itemSelectionChanged.connect(self.show_detail);self.tree.itemDoubleClicked.connect(lambda *_:self.edit_task());split.addWidget(self.tree)
        self.detail=QPlainTextEdit();self.detail.setReadOnly(True);split.addWidget(self.detail);split.setSizes([820,330])
        destination=QHBoxLayout();destination.addWidget(QLabel('Pasta de saída'));self.destination=QLineEdit();default=project_root()/'exports'/'agentes';default.mkdir(parents=True,exist_ok=True);self.destination.setText(str(default));destination.addWidget(self.destination,1)
        self.choose=QPushButton('Escolher');self.choose.clicked.connect(self.choose_destination);destination.addWidget(self.choose);layout.addLayout(destination)
        actions=QHBoxLayout();self.start=QPushButton('Iniciar agentes');self.start.clicked.connect(self.start_run);actions.addWidget(self.start)
        self.cancel=QPushButton('Cancelar execução');self.cancel.setEnabled(False);self.cancel.clicked.connect(self.cancel_run);actions.addWidget(self.cancel)
        self.open=QPushButton('Abrir arquivos');self.open.setEnabled(False);self.open.clicked.connect(self.open_files);actions.addWidget(self.open);actions.addStretch()
        self.status=QLabel('Pronto para configurar');actions.addWidget(self.status);layout.addLayout(actions)
        history=QHBoxLayout();history.addWidget(QLabel('Histórico local'));self.history=QComboBox();self.history.activated.connect(self.load_history);history.addWidget(self.history,1);layout.addLayout(history)
        self.updated.connect(self.render_run);self.ended.connect(self.finished)
        self.timer=QTimer(self);self.timer.setInterval(500);self.timer.timeout.connect(self.refresh_times)
        self.load_template();self.refresh_history()
    def load_template(self):
        self.tasks=[AgentTask('codigo','Programador','Crie uma aplicação web funcional e completa em um único HTML autocontido, conforme objetivo. Não diga que testou. Inclua crédito ChilenoAPPs.',('index.html',)),
                    AgentTask('documentacao','Documentador','Documente o projeto descrito: instruções para abrir um HTML autocontido, controles esperados e limitações. Não invente testes nem APIs.',('README.md',)),
                    AgentTask('revisao','Revisor','Revise os arquivos recebidos em relação ao objetivo. Aponte falhas, inconsistências na documentação, limitações e passos de teste manual. Não afirme ter executado testes.',('REVIEW.md',),('codigo','documentacao'))]
        self.current=None;self.render_plan()
    def selected_id(self):
        item=self.tree.currentItem();return item.data(0,Qt.ItemDataRole.UserRole) if item else None
    def render_plan(self):
        self.tree.clear()
        for task in self.tasks:
            item=QTreeWidgetItem([task.id+' · '+task.model,'Configurado',', '.join(task.depends),', '.join(task.files),'']);item.setData(0,Qt.ItemDataRole.UserRole,task.id);self.tree.addTopLevelItem(item)
        self.detail.setPlainText('Edite as funções, modelos, arquivos e dependências antes de iniciar. Os agentes trabalham em uma pasta nova por execução.');self.open.setEnabled(False)
        if self.tree.topLevelItemCount():self.tree.setCurrentItem(self.tree.topLevelItem(0))
    def add_task(self):
        if len(self.tasks)>=8:QMessageBox.information(self,'Agentes','Limite de oito agentes.');return
        dialog=TaskEditor(AgentTask('agente'+str(len(self.tasks)+1),'Especialista','',('resultado'+str(len(self.tasks)+1)+'.md',)),self)
        if dialog.exec():self.tasks.append(dialog.value());self.current=None;self.render_plan()
    def edit_task(self):
        if self.thread and self.thread.is_alive():return
        key=self.selected_id();index=next((i for i,t in enumerate(self.tasks) if t.id==key),None)
        if index is None:return
        dialog=TaskEditor(self.tasks[index],self)
        if dialog.exec():self.tasks[index]=dialog.value();self.current=None;self.render_plan()
    def remove_task(self):
        key=self.selected_id();self.tasks=[t for t in self.tasks if t.id!=key];self.current=None;self.render_plan()
    def choose_destination(self):
        folder=QFileDialog.getExistingDirectory(self,'Pasta para novas execuções',self.destination.text())
        if folder:self.destination.setText(folder)
    def set_brief(self,text):
        if not (self.thread and self.thread.is_alive()):self.brief.setPlainText(str(text)[:12000])
    def start_run(self):
        if self.thread and self.thread.is_alive():return
        try:
            validate_tasks(self.tasks)
            brief=self.brief.toPlainText().strip()
            if not self.destination.text().strip():raise ValueError('Escolha uma pasta de saída.')
            folder=Path(self.destination.text()).expanduser().resolve()
            if not brief or len(brief)>12000:raise ValueError('Informe o objetivo (até 12000 caracteres).')
            if not folder.is_dir():raise ValueError('Escolha uma pasta existente.')
            config=self.config_loader()
            from core.agent_workspace import ClaudeArtifactAgent
            for task in self.tasks:ClaudeArtifactAgent(config).command(task)
        except Exception as exc:QMessageBox.warning(self,'Não foi possível iniciar',str(exc));return
        tasks=list(self.tasks);parallel=self.parallel.value();self.stop.clear();self.current=None;self.set_running(True)
        def worker():
            async def execute():
                self.loop=asyncio.get_running_loop();engine=AgentWorkspace(self.store,config=config)
                self.job=asyncio.create_task(engine.run(brief,tasks,folder,parallel,self.updated.emit))
                if self.stop.is_set():self.job.cancel()
                try:await self.job
                except asyncio.CancelledError:pass
                finally:self.job=None
            error=''
            try:asyncio.run(execute())
            except Exception:error='Falha na execução. Verifique a pasta de saída e a configuração do Claude Code.'
            finally:self.loop=None;self.ended.emit(error)
        self.thread=threading.Thread(target=worker,daemon=True);self.thread.start();self.timer.start()
    def set_running(self,value):
        for widget in (self.add,self.edit,self.remove,self.template,self.parallel,self.brief,self.destination,self.choose,self.start,self.history):widget.setEnabled(not value)
        self.cancel.setEnabled(value)
    def cancel_run(self):
        self.stop.set();self.status.setText('Cancelando agentes…')
        loop,job=self.loop,self.job
        if loop and job:
            try:loop.call_soon_threadsafe(job.cancel)
            except RuntimeError:pass
    def shutdown(self):
        self.cancel_run();self.timer.stop()
        if self.thread and self.thread.is_alive():self.thread.join(3)
    def render_run(self,run):
        self.current=run
        ids=[self.tree.topLevelItem(i).data(0,Qt.ItemDataRole.UserRole) for i in range(self.tree.topLevelItemCount())]
        if ids!=list(run['tasks']):
            self.tree.clear()
            for key in run['tasks']:
                item=QTreeWidgetItem();item.setData(0,Qt.ItemDataRole.UserRole,key);self.tree.addTopLevelItem(item)
        for i,(key,task) in enumerate(run['tasks'].items()):
            item=self.tree.topLevelItem(i);item.setText(0,key+' · '+task['model']);item.setText(1,STATES.get(task['state'],task['state']));item.setText(2,', '.join(task['depends']));item.setText(3,', '.join(task['files']))
        succeeded=sum(t['state']=='succeeded' for t in run['tasks'].values());active=sum(t['state']=='running' for t in run['tasks'].values())
        self.status.setText(f"{succeeded}/{len(run['tasks'])} concluídos · {active} trabalhando · {STATES.get(run['state'],run['state'])}")
        self.open.setEnabled(Path(run['folder']).is_dir());self.refresh_times();self.show_detail()
    def refresh_times(self):
        if not self.current:return
        for i,task in enumerate(self.current['tasks'].values()):
            seconds=int((task.get('ended') or time.time())-(task.get('started') or time.time()))
            self.tree.topLevelItem(i).setText(4,f"{max(0,seconds)} s · {task.get('characters',0)} caracteres")
    def show_detail(self):
        key=self.selected_id()
        if self.current and key in self.current['tasks']:
            task=self.current['tasks'][key]
        else:
            selected=next((t for t in self.tasks if t.id==key),None)
            if not selected:return
            task={'role':selected.role,'prompt':selected.prompt,'files':selected.files,'summary':'Configurado; ainda não executado.'}
        text=f"{task['role']}\n\n{task['prompt']}\n\n{task.get('summary') or 'Aguardando resultado…'}\n\nArquivos: "+', '.join(task['files'])
        if text!=self.detail.toPlainText():self.detail.setPlainText(text)
    def finished(self,error):
        self.timer.stop();self.set_running(False)
        if error:self.status.setText(error)
        elif self.current is None:self.status.setText('Execução cancelada antes de iniciar.')
        self.refresh_history()
    def refresh_history(self):
        self.history.clear();self.history.addItem('Selecione uma execução…',None)
        for run in self.store.recent():self.history.addItem(time.strftime('%d/%m %H:%M',time.localtime(run['created']))+' · '+run['brief'][:55]+' · '+STATES.get(run['state'],run['state']),run)
    def load_history(self,index):
        run=self.history.itemData(index)
        if not run:return
        if run['state']=='running':
            run['state']='interrupted'
            for task in run['tasks'].values():
                if task['state'] not in ('succeeded','failed','blocked','cancelled'):task['state']='interrupted'
        self.tasks=[AgentTask(t['id'],t['role'],t['prompt'],tuple(t['files']),tuple(t['depends']),t['model']) for t in run['tasks'].values()]
        self.brief.setPlainText(run['brief']);self.render_run(run)
    def open_files(self):
        if self.current:QDesktopServices.openUrl(QUrl.fromLocalFile(self.current.get('project') or self.current['folder']))
    def closeEvent(self,event):self.hide();event.ignore()
