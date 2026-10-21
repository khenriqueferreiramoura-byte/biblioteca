import os
from datetime import date
from functools import wraps
import mysql.connector
from mysql.connector import Error
from flask import Flask, request, redirect, url_for, session, flash, render_template_string

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'chave-local-altere-antes-de-publicar')
DB = dict(host=os.getenv('DB_HOST','localhost'), database=os.getenv('DB_NAME','BIBLIOTECA_INTELIGENTE'), user=os.getenv('DB_USER','root'), password=os.getenv('DB_PASSWORD',''), port=int(os.getenv('DB_PORT','3307')))
LOGIN_USER = os.getenv('APP_USER','admin')
LOGIN_PASS = os.getenv('APP_PASSWORD','biblioteca123')

BASE = '''<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{ title }} · Biblioteca Inteligente</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f6fb;color:#172b45;font:14px Arial,sans-serif}.layout{display:flex;min-height:100vh}.side{width:230px;background:#102b4d;color:white;padding:22px 14px;display:flex;flex-direction:column;gap:8px}.brand{font-size:20px;font-weight:bold;padding:10px 8px 25px}.side a{color:#dce9fa;text-decoration:none;padding:12px;border-radius:8px}.side a:hover,.side a.active{background:#285384}.logout{margin-top:auto}.main{flex:1;min-width:0}.top{background:white;padding:22px 28px;border-bottom:1px solid #dce5f0;display:flex;justify-content:space-between}.content{padding:25px;max-width:1500px;margin:auto}h1{font-size:20px;margin:0;color:#122e51}h2{margin:0 0 8px;color:#122e51}h3{margin:0 0 15px}.muted{color:#718096}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:13px;margin:18px 0}.card,.panel{background:white;border:1px solid #dce5f0;border-radius:12px;padding:18px;margin-bottom:16px}.card span{color:#718096;font-size:12px}.card strong{display:block;font-size:28px;margin-top:12px;color:#1e66bd}.btn{border:0;border-radius:7px;background:#2677df;color:white;padding:10px 14px;text-decoration:none;display:inline-block;cursor:pointer;font-weight:bold;font-size:12px}.btn.light{background:#e7f0ff;color:#1b5aa7}input,select{width:100%;padding:11px;border:1px solid #cbd8e8;border-radius:7px;background:white}label{display:block;font-size:12px;font-weight:bold;margin:12px 0 6px}.formgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;align-items:end}.tablewrap{overflow:auto}table{border-collapse:collapse;width:100%;min-width:600px;font-size:12px}th,td{text-align:left;padding:12px;border-bottom:1px solid #e8eef6}th{background:#f3f7fc;color:#53677f}td form{display:inline}.action{display:flex;gap:10px;align-items:center}.danger{background:none;border:0;color:#b42318;cursor:pointer;font-weight:bold}.msg{padding:12px;border-radius:7px;margin-bottom:10px}.sucesso{background:#dcfce7;color:#166534}.erro{background:#fee2e2;color:#991b1b}.pill{padding:5px 8px;border-radius:20px;background:#dbeafe;color:#1759a5;font-size:10px;font-weight:bold}.pill.done{background:#d9f8e8;color:#08764e}.login{min-height:100vh;display:grid;place-items:center;background:linear-gradient(135deg,#102b4d,#245687);padding:20px}.loginbox{width:min(410px,100%);background:white;border-radius:16px;padding:32px}.loginbox h1{text-align:center;margin-bottom:8px}.loginbox p{text-align:center;color:#718096}.loginbox button{width:100%;margin-top:18px}.empty{text-align:center;padding:24px;color:#718096}footer{text-align:center;color:#9aa8b9;font-size:10px;padding:15px}@media(max-width:700px){.layout{display:block}.side{width:100%;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));padding:10px}.brand{grid-column:1/-1;padding:8px}.logout{margin:0}.top{padding:16px}.content{padding:12px}.formgrid{grid-template-columns:1fr}}
</style></head><body>{% if logged %}<div class="layout"><aside class="side"><div class="brand">▤ Biblioteca<br>Inteligente</div><a class="{{ 'active' if page=='inicio' else '' }}" href="{{ url_for('inicio') }}">⌂ Visão geral</a><a class="{{ 'active' if page=='livros' else '' }}" href="{{ url_for('livros') }}">▤ Livros</a><a class="{{ 'active' if page=='autores' else '' }}" href="{{ url_for('autores') }}">✎ Autores</a><a class="{{ 'active' if page=='alunos' else '' }}" href="{{ url_for('alunos') }}">♟ Alunos</a><a class="{{ 'active' if page=='emprestimos' else '' }}" href="{{ url_for('emprestimos') }}">⇥ Empréstimos</a><a class="{{ 'active' if page=='devolucoes' else '' }}" href="{{ url_for('devolucoes') }}">↩ Devoluções</a><a class="{{ 'active' if page=='historico' else '' }}" href="{{ url_for('historico') }}">◷ Histórico</a><a class="logout" href="{{ url_for('sair') }}">Sair do sistema</a></aside><main class="main"><header class="top"><h1>{{ title }}</h1><span>Olá, {{ session.get('usuario','admin') }}</span></header><section class="content">{% with messages=get_flashed_messages(with_categories=true) %}{% for cat,msg in messages %}<div class="msg {{cat}}">{{msg}}</div>{% endfor %}{% endwith %}{% block content %}{% endblock %}<footer>Biblioteca Inteligente · Projeto acadêmico</footer></section></main></div>{% else %}<main class="login"><section class="loginbox"><h1>▤ Biblioteca Inteligente</h1><p>Entre para gerenciar o acervo</p>{% with messages=get_flashed_messages(with_categories=true) %}{% for cat,msg in messages %}<div class="msg {{cat}}">{{msg}}</div>{% endfor %}{% endwith %}<form method="post"><label>Usuário</label><input name="usuario" required autofocus><label>Senha</label><input type="password" name="senha" required><button class="btn">Entrar</button></form><p>Teste: admin / biblioteca123</p></section></main>{% endif %}</body></html>'''

# Pages are inserted into the common layout template.
def page(title, page_name, body, **context):
    template = BASE.replace('{% block content %}{% endblock %}', body)
    return render_template_string(template, title=title, page=page_name, logged=True, **context)

def conn(): return mysql.connector.connect(**DB)
def query(sql, args=()):
    c=conn(); cur=None
    try:
        cur=c.cursor(dictionary=True); cur.execute(sql,args); return cur.fetchall()
    finally:
        if cur: cur.close()
        c.close()
def change(sql,args=()):
    c=conn(); cur=None
    try:
        cur=c.cursor(); cur.execute(sql,args); c.commit(); return cur.lastrowid,cur.rowcount
    except Exception:
        c.rollback(); raise
    finally:
        if cur: cur.close()
        c.close()
def required(f):
    @wraps(f)
    def w(*a,**k):
        if not session.get('ok'): return redirect(url_for('login'))
        return f(*a,**k)
    return w
@app.template_filter('brdate')
def brdate(v): return v.strftime('%d/%m/%Y') if v and hasattr(v,'strftime') else (v or '—')
@app.template_filter('brl')
def brl(v): return ('R$ {:,.2f}'.format(float(v or 0))).replace(',','X').replace('.',',').replace('X','.')

@app.route('/',methods=['GET','POST'])
def login():
    if session.get('ok'): return redirect(url_for('inicio'))
    if request.method=='POST':
        if request.form.get('usuario','').strip()==LOGIN_USER and request.form.get('senha','')==LOGIN_PASS:
            session.clear(); session['ok']=True; session['usuario']=LOGIN_USER; return redirect(url_for('inicio'))
        flash('Usuário ou senha incorretos.','erro')
    return render_template_string(BASE,title='Entrar',page='',logged=False)
@app.route('/sair')
def sair(): session.clear(); return redirect(url_for('login'))

@app.route('/inicio')
@required
def inicio():
    try:
        counts={k:query(sql)[0]['n'] for k,sql in {
            'livros':'SELECT COUNT(*) n FROM LIVROS','autores':'SELECT COUNT(*) n FROM AUTORES','alunos':'SELECT COUNT(*) n FROM ALUNOS',
            'ativos':"SELECT COUNT(*) n FROM EMPRESTIMO WHERE STATUS='Emprestado'",
            'disponiveis':"SELECT COUNT(*) n FROM LIVROS L WHERE NOT EXISTS (SELECT 1 FROM EMPRESTIMO E WHERE E.ID_LIVRO=L.ID_LIVRO AND E.STATUS='Emprestado')"}.items()}
        recent=query("SELECT E.ID_EMPRESTIMO,E.DATA_EMPREST,E.STATUS,A.NOME ALUNO,L.TITULO LIVRO FROM EMPRESTIMO E JOIN ALUNOS A ON A.ID_ALUNO=E.ID_ALUNO JOIN LIVROS L ON L.ID_LIVRO=E.ID_LIVRO ORDER BY E.ID_EMPRESTIMO DESC LIMIT 6")
    except Error as e: flash(f'Erro no banco: {e}. Execute atualizar_banco.sql.','erro'); counts=dict(livros='—',autores='—',alunos='—',ativos='—',disponiveis='—'); recent=[]
    body='''<div class="panel"><h2>Bem-vindo à Biblioteca Inteligente</h2><p>Gerencie livros, autores, alunos, empréstimos e devoluções em um só lugar.</p></div><div class="cards">{% for label,key in [('Livros','livros'),('Autores','autores'),('Alunos','alunos'),('Empréstimos ativos','ativos'),('Livros disponíveis','disponiveis')] %}<div class="card"><span>{{label}}</span><strong>{{counts[key]}}</strong></div>{% endfor %}</div><div class="panel"><h3>Movimentações recentes</h3><div class="tablewrap"><table><tr><th>ID</th><th>Aluno</th><th>Livro</th><th>Data</th><th>Status</th></tr>{% for x in recent %}<tr><td>{{x.ID_EMPRESTIMO}}</td><td>{{x.ALUNO}}</td><td>{{x.LIVRO}}</td><td>{{x.DATA_EMPREST|brdate}}</td><td><span class="pill {{'done' if x.STATUS=='Devolvido' else ''}}">{{x.STATUS}}</span></td></tr>{% else %}<tr><td colspan="5" class="empty">Sem registros.</td></tr>{% endfor %}</table></div></div>'''
    return page('Visão geral','inicio',body,counts=counts,recent=recent)

CONFIG={
'livros':dict(table='LIVROS',pk='ID_LIVRO',fields=[('titulo','TITULO','Título',45),('genero','GENERO','Gênero',20),('preco','PREÇO','Preço (R$)',None)], select='SELECT ID_LIVRO,TITULO,GENERO,`PREÇO` AS PRECO FROM LIVROS ORDER BY TITULO', headers=['ID','Título','Gênero','Preço'], keys=['ID_LIVRO','TITULO','GENERO','PRECO']),
'autores':dict(table='AUTORES',pk='ID_AUTOR',fields=[('nome','NOME','Nome',30),('nascimento','DATA_NASCI','Nascimento',None),('id_livro','ID_LIVRO','ID do livro associado',None)],select='SELECT A.ID_AUTOR,A.NOME,A.DATA_NASCI,A.ID_LIVRO,L.TITULO AS LIVRO FROM AUTORES A LEFT JOIN LIVROS L ON L.ID_LIVRO=A.ID_LIVRO ORDER BY A.NOME',headers=['ID','Nome','Nascimento','Livro'],keys=['ID_AUTOR','NOME','DATA_NASCI','LIVRO']),
'alunos':dict(table='ALUNOS',pk='ID_ALUNO',fields=[('nome','NOME','Nome',30),('cpf','CPF_ALUN','CPF',17),('matr','MATR','Matrícula',None)],select='SELECT ID_ALUNO,NOME,CPF_ALUN,MATR FROM ALUNOS ORDER BY NOME',headers=['ID','Nome','CPF','Matrícula'],keys=['ID_ALUNO','NOME','CPF_ALUN','MATR'])}

def crud(entity):
    cfg=CONFIG[entity]
    if request.method=='POST':
        action=request.form.get('action','create'); vals=[]
        for formkey,col,label,maxlen in cfg['fields']:
            v=request.form.get(formkey,'').strip()
            if formkey in ('preco','matr','id_livro') and v=='': v=None
            if formkey=='nascimento' and v=='': v=None
            vals.append(v)
        try:
            if action=='update':
                sets=', '.join((f'`{f[1]}`=%s' if f[1]=='PREÇO' else f'{f[1]}=%s') for f in cfg['fields'])
                change(f"UPDATE {cfg['table']} SET {sets} WHERE {cfg['pk']}=%s",tuple(vals+[int(request.form['id'])]))
                flash('Registro atualizado com sucesso.','sucesso')
            else:
                cols=', '.join(f'`{f[1]}`' if f[1]=='PREÇO' else f[1] for f in cfg['fields'])
                marks=', '.join(['%s']*len(vals)); change(f"INSERT INTO {cfg['table']} ({cols}) VALUES ({marks})",tuple(vals))
                flash('Registro cadastrado com sucesso.','sucesso')
        except (Error,ValueError,KeyError) as e: flash(f'Não foi possível salvar: {e}','erro')
        return redirect(url_for(entity))
    try:
        rows=query(cfg['select']); editid=request.args.get('edit',type=int); edit=next((r for r in rows if r[cfg['pk']]==editid),None)
    except Error as e: rows=[]; edit=None; flash(f'Erro ao consultar: {e}','erro')
    form=''.join(f'<div><label>{label}</label><input name="{key}" {"required" if key not in ("preco","nascimento","id_livro","matr") else ""} type="{"date" if key=="nascimento" else "number" if key in ("preco","matr","id_livro") else "text"}" value="{{{{ edit[\'{'PRECO' if col=='PREÇO' else col}\'] if edit and edit[\'{'PRECO' if col=='PREÇO' else col}\'] is not none else \'\' }}}}" {"step=\"0.01\" min=\"0\"" if key=="preco" else ""}></div>' for key,col,label,_ in cfg['fields'])
    tablehead=''.join(f'<th>{h}</th>' for h in cfg['headers'])+'<th>Ações</th>'
    tablecells=''.join(f'<td>{{{{ x[\'{k}\']|brdate if k==\'DATA_NASCI\' else x[\'{k}\']|brl if k==\'PRECO\' else x[\'{k}\'] or \'—\' }}}}</td>' for k in cfg['keys'])
    body=f'''<div class="panel"><h2>{{{{ 'Editar' if edit else 'Cadastrar' }}}} {entity[:-1] if entity!='alunos' else 'aluno'}</h2><form method="post"><input type="hidden" name="action" value="{{{{ 'update' if edit else 'create' }}}}"><input type="hidden" name="id" value="{{{{ edit['{cfg['pk']}'] if edit else '' }}}}"><div class="formgrid">{form}<div><button class="btn">{{{{ 'Salvar alterações' if edit else 'Cadastrar' }}}}</button> {{% if edit %}}<a class="btn light" href="{{{{ url_for('{entity}') }}}}">Cancelar</a>{{% endif %}}</div></div></form></div><div class="panel"><h3>Registros cadastrados ({{{{rows|length}}}})</h3><div class="tablewrap"><table><tr>{tablehead}</tr>{{% for x in rows %}}<tr>{tablecells}<td class="action"><a href="{{{{ url_for('{entity}',edit=x['{cfg['pk']}']) }}}}">Editar</a><form method="post" action="{{{{ url_for('delete_record',entity='{entity}',id=x['{cfg['pk']}']) }}}}" onsubmit="return confirm('Confirma excluir este registro?')"><button class="danger">Excluir</button></form></td></tr>{{% else %}}<tr><td colspan="{len(cfg['keys'])+1}" class="empty">Nenhum registro cadastrado.</td></tr>{{% endfor %}}</table></div></div>'''
    return page(entity.capitalize(),' '+entity,body,rows=rows,edit=edit)

@app.route('/livros',methods=['GET','POST'])
@required
def livros(): return crud('livros')
@app.route('/autores',methods=['GET','POST'])
@required
def autores(): return crud('autores')
@app.route('/alunos',methods=['GET','POST'])
@required
def alunos(): return crud('alunos')
@app.route('/<entity>/excluir/<int:id>',methods=['POST'])
@required

def delete_record(entity, id):
    if entity not in CONFIG:
        return redirect(url_for('inicio'))

    cfg = CONFIG[entity]

    try:
        # Verifica se o livro possui empréstimos registrados
        if entity == 'livros':
            emprestimos = query(
                'SELECT ID_EMPRESTIMO FROM EMPRESTIMO '
                'WHERE ID_LIVRO = %s LIMIT 1',
                (id,)
            )

            if emprestimos:
                flash(
                    'Este livro possui histórico de empréstimos '
                    'e não pode ser excluído.',
                    'erro'
                )
                return redirect(url_for(entity))

        # Verifica se o aluno possui empréstimos registrados
        if entity == 'alunos':
            emprestimos = query(
                'SELECT ID_EMPRESTIMO FROM EMPRESTIMO '
                'WHERE ID_ALUNO = %s LIMIT 1',
                (id,)
            )

            if emprestimos:
                flash(
                    'Este aluno possui histórico de empréstimos. '
                    'O cadastro foi mantido para preservar o histórico.',
                    'erro'
                )
                return redirect(url_for(entity))

        # Exclui o registro somente se não houver bloqueio
        change(
            f"DELETE FROM {cfg['table']} WHERE {cfg['pk']} = %s",
            (id,)
        )

        flash('Registro excluído com sucesso!', 'sucesso')

    except Error as e:
        flash(
            f'Não foi possível excluir o registro. '
            f'Verifique se existem vínculos com outros registros. Detalhes: {e}',
            'erro'
        )

    return redirect(url_for(entity))
@app.route('/emprestimos', methods=['GET', 'POST'])
def emprestimos():
    if request.method=='POST':
        try:
            aid=int(request.form['id_aluno']); lid=int(request.form['id_livro']); val=float(request.form.get('valor') or 0); dt=request.form.get('data') or date.today().isoformat()
            if not query('SELECT ID_ALUNO FROM ALUNOS WHERE ID_ALUNO=%s',(aid,)): flash('Aluno não encontrado.','erro')
            elif not query('SELECT ID_LIVRO FROM LIVROS WHERE ID_LIVRO=%s',(lid,)): flash('Livro não encontrado.','erro')
            elif query("SELECT ID_EMPRESTIMO FROM EMPRESTIMO WHERE ID_LIVRO=%s AND STATUS='Emprestado'",(lid,)): flash('Este livro já está emprestado.','erro')
            else: change("INSERT INTO EMPRESTIMO (VALOR,DATA_EMPREST,ID_LIVRO,ID_ALUNO,STATUS) VALUES (%s,%s,%s,%s,'Emprestado')",(val,dt,lid,aid)); flash('Empréstimo registrado!','sucesso')
        except (Error,ValueError,KeyError) as e: flash(f'Erro ao registrar empréstimo: {e}','erro')
        return redirect(url_for('emprestimos'))
    try:
        alunos_l=query('SELECT ID_ALUNO,NOME FROM ALUNOS ORDER BY NOME')
        livros_l=query("SELECT L.ID_LIVRO,L.TITULO FROM LIVROS L WHERE NOT EXISTS (SELECT 1 FROM EMPRESTIMO E WHERE E.ID_LIVRO=L.ID_LIVRO AND E.STATUS='Emprestado') ORDER BY L.TITULO")
        rows=query('SELECT E.ID_EMPRESTIMO,E.DATA_EMPREST,E.STATUS,E.VALOR,A.NOME ALUNO,L.TITULO LIVRO FROM EMPRESTIMO E JOIN ALUNOS A ON A.ID_ALUNO=E.ID_ALUNO JOIN LIVROS L ON L.ID_LIVRO=E.ID_LIVRO ORDER BY E.ID_EMPRESTIMO DESC')
    except Error as e: flash(f'Erro ao consultar empréstimos: {e}','erro'); alunos_l=[]; livros_l=[]; rows=[]
    body='''<div class="panel"><h2>Novo empréstimo</h2><form method="post" class="formgrid"><div><label>Aluno</label><select name="id_aluno" required><option value="">Selecione</option>{% for a in alunos_l %}<option value="{{a.ID_ALUNO}}">{{a.NOME}} ({{a.ID_ALUNO}})</option>{% endfor %}</select></div><div><label>Livro disponível</label><select name="id_livro" required><option value="">Selecione</option>{% for l in livros_l %}<option value="{{l.ID_LIVRO}}">{{l.TITULO}}</option>{% endfor %}</select></div><div><label>Data</label><input type="date" name="data" value="{{hoje}}" required></div><div><label>Valor (R$)</label><input type="number" name="valor" min="0" step="0.01" value="0.00" required></div><div><button class="btn" {% if not alunos_l or not livros_l %}disabled{% endif %}>Registrar empréstimo</button></div></form></div><div class="panel"><h3>Histórico</h3><div class="tablewrap"><table><tr><th>ID</th><th>Aluno</th><th>Livro</th><th>Data</th><th>Valor</th><th>Status</th></tr>{% for x in rows %}<tr><td>{{x.ID_EMPRESTIMO}}</td><td>{{x.ALUNO}}</td><td>{{x.LIVRO}}</td><td>{{x.DATA_EMPREST|brdate}}</td><td>{{x.VALOR|brl}}</td><td><span class="pill {{'done' if x.STATUS=='Devolvido' else ''}}">{{x.STATUS}}</span></td></tr>{% else %}<tr><td colspan="6" class="empty">Sem empréstimos.</td></tr>{% endfor %}</table></div></div>'''
    return page('Empréstimos','emprestimos',body,alunos_l=alunos_l,livros_l=livros_l,rows=rows,hoje=date.today().isoformat())

@app.route('/devolucoes',methods=['GET','POST'])
@required
def devolucoes():
    if request.method=='POST':
        try:
            eid=int(request.form['id_emprestimo']); dt=request.form.get('data') or date.today().isoformat(); _,n=change("UPDATE EMPRESTIMO SET STATUS='Devolvido',DATA_DEVOLUCAO=%s WHERE ID_EMPRESTIMO=%s AND STATUS='Emprestado'",(dt,eid)); flash('Devolução registrada; livro disponível novamente.' if n else 'Empréstimo não encontrado ou já devolvido.','sucesso' if n else 'erro')
        except (Error,ValueError,KeyError) as e: flash(f'Erro na devolução: {e}','erro')
        return redirect(url_for('devolucoes'))
    try: rows=query("SELECT E.ID_EMPRESTIMO,E.DATA_EMPREST,A.NOME ALUNO,L.TITULO LIVRO FROM EMPRESTIMO E JOIN ALUNOS A ON A.ID_ALUNO=E.ID_ALUNO JOIN LIVROS L ON L.ID_LIVRO=E.ID_LIVRO WHERE E.STATUS='Emprestado' ORDER BY E.ID_EMPRESTIMO")
    except Error as e: flash(f'Erro ao consultar: {e}','erro'); rows=[]
    body='''<div class="panel"><h2>Registrar devolução</h2><form method="post" class="formgrid"><div><label>Empréstimo ativo</label><select name="id_emprestimo" required><option value="">Selecione</option>{% for x in rows %}<option value="{{x.ID_EMPRESTIMO}}">#{{x.ID_EMPRESTIMO}} · {{x.ALUNO}} — {{x.LIVRO}}</option>{% endfor %}</select></div><div><label>Data da devolução</label><input type="date" name="data" value="{{hoje}}" required></div><div><button class="btn" {% if not rows %}disabled{% endif %}>Confirmar devolução</button></div></form></div><div class="panel"><h3>Empréstimos ativos</h3><div class="tablewrap"><table><tr><th>ID</th><th>Aluno</th><th>Livro</th><th>Data</th></tr>{% for x in rows %}<tr><td>{{x.ID_EMPRESTIMO}}</td><td>{{x.ALUNO}}</td><td>{{x.LIVRO}}</td><td>{{x.DATA_EMPREST|brdate}}</td></tr>{% else %}<tr><td colspan="4" class="empty">Nenhum empréstimo ativo.</td></tr>{% endfor %}</table></div></div>'''
    return page('Devoluções','devolucoes',body,rows=rows,hoje=date.today().isoformat())

@app.route('/historico')
@required
def historico():
    try: rows=query('SELECT E.ID_EMPRESTIMO,E.DATA_EMPREST,E.DATA_DEVOLUCAO,E.STATUS,E.VALOR,A.NOME ALUNO,L.TITULO LIVRO FROM EMPRESTIMO E JOIN ALUNOS A ON A.ID_ALUNO=E.ID_ALUNO JOIN LIVROS L ON L.ID_LIVRO=E.ID_LIVRO ORDER BY E.ID_EMPRESTIMO DESC')
    except Error as e: flash(f'Erro ao consultar histórico: {e}','erro'); rows=[]
    body='''<div class="panel"><h2>Histórico completo</h2><div class="tablewrap"><table><tr><th>ID</th><th>Aluno</th><th>Livro</th><th>Empréstimo</th><th>Devolução</th><th>Valor</th><th>Status</th></tr>{% for x in rows %}<tr><td>#{{x.ID_EMPRESTIMO}}</td><td>{{x.ALUNO}}</td><td>{{x.LIVRO}}</td><td>{{x.DATA_EMPREST|brdate}}</td><td>{{x.DATA_DEVOLUCAO|brdate}}</td><td>{{x.VALOR|brl}}</td><td><span class="pill {{'done' if x.STATUS=='Devolvido' else ''}}">{{x.STATUS}}</span></td></tr>{% else %}<tr><td colspan="7" class="empty">Nenhum registro.</td></tr>{% endfor %}</table></div></div>'''
    return page('Histórico','historico',body,rows=rows)

if __name__=='__main__': app.run(debug=True)
