import os
from datetime import date
from functools import wraps

import mysql.connector
from mysql.connector import Error
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "troque-esta-chave-antes-de-publicar")

DB = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "BIBLIOTECA_INTELIGENTE"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "port": int(os.getenv("DB_PORT", "3307")),
}
LOGIN_USER = os.getenv("APP_USER", "admin")
LOGIN_PASS = os.getenv("APP_PASSWORD", "biblioteca123")


def conn():
    return mysql.connector.connect(**DB)


def query(sql, args=()):
    connection = conn()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql, args)
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        connection.close()


def change(sql, args=()):
    connection = conn()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(sql, args)
        connection.commit()
        return cursor.lastrowid, cursor.rowcount
    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        connection.close()


def required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("ok"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.template_filter("brdate")
def brdate(value):
    return value.strftime("%d/%m/%Y") if value and hasattr(value, "strftime") else (value or "—")


@app.template_filter("brl")
def brl(value):
    return ("R$ {:,.2f}".format(float(value or 0))).replace(",", "X").replace(".", ",").replace("X", ".")


@app.route("/", methods=["GET", "POST"])
def login():
    if session.get("ok"):
        return redirect(url_for("inicio"))
    if request.method == "POST":
        if request.form.get("usuario", "").strip() == LOGIN_USER and request.form.get("senha", "") == LOGIN_PASS:
            session.clear()
            session["ok"] = True
            session["usuario"] = LOGIN_USER
            return redirect(url_for("inicio"))
        flash("Usuário ou senha incorretos.", "erro")
    return render_template("login.html")


@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("login"))


@app.route("/inicio")
@required
def inicio():
    counts = {"livros": "—", "autores": "—", "alunos": "—", "ativos": "—", "disponiveis": "—"}
    recent = []
    try:
        count_sql = {
            "livros": "SELECT COUNT(*) n FROM LIVROS",
            "autores": "SELECT COUNT(*) n FROM AUTORES",
            "alunos": "SELECT COUNT(*) n FROM ALUNOS",
            "ativos": "SELECT COUNT(*) n FROM EMPRESTIMO WHERE STATUS='Emprestado'",
            "disponiveis": """SELECT COUNT(*) n FROM LIVROS L
                WHERE NOT EXISTS (SELECT 1 FROM EMPRESTIMO E
                WHERE E.ID_LIVRO=L.ID_LIVRO AND E.STATUS='Emprestado')""",
        }
        counts = {key: query(sql)[0]["n"] for key, sql in count_sql.items()}
        recent = query("""SELECT E.ID_EMPRESTIMO, E.DATA_EMPREST, E.STATUS,
                          A.NOME ALUNO, L.TITULO LIVRO
                          FROM EMPRESTIMO E
                          JOIN ALUNOS A ON A.ID_ALUNO=E.ID_ALUNO
                          JOIN LIVROS L ON L.ID_LIVRO=E.ID_LIVRO
                          ORDER BY E.ID_EMPRESTIMO DESC LIMIT 8""")
    except Error as exc:
        flash(f"Não foi possível carregar os indicadores. Confira a conexão e as tabelas: {exc}", "erro")
    return render_template("dashboard.html", title="Visão geral", page="inicio", counts=counts, recent=recent)


CONFIG = {
    "livros": {
        "table": "LIVROS", "pk": "ID_LIVRO",
        "fields": [
            ("titulo", "TITULO", "Título", "text", True),
            ("genero", "GENERO", "Gênero", "text", True),
            ("preco", "PREÇO", "Preço (R$)", "number", False),
            ("capa_url", "CAPA_URL", "URL da capa (opcional)", "url", False),
        ],
        "select": "SELECT ID_LIVRO,TITULO,GENERO,`PREÇO` AS PRECO,CAPA_URL FROM LIVROS ORDER BY TITULO",
        "headers": ["Capa", "ID", "Título", "Gênero", "Preço"],
        "keys": ["CAPA_URL", "ID_LIVRO", "TITULO", "GENERO", "PRECO"],
        "search": "TITULO LIKE %s OR GENERO LIKE %s",
    },
    "autores": {
        "table": "AUTORES", "pk": "ID_AUTOR",
        "fields": [
            ("nome", "NOME", "Nome", "text", True),
            ("nascimento", "DATA_NASCI", "Nascimento", "date", False),
            ("id_livro", "ID_LIVRO", "ID do livro associado", "number", False),
        ],
        "select": """SELECT A.ID_AUTOR,A.NOME,A.DATA_NASCI,A.ID_LIVRO,L.TITULO AS LIVRO
                     FROM AUTORES A LEFT JOIN LIVROS L ON L.ID_LIVRO=A.ID_LIVRO
                     ORDER BY A.NOME""",
        "headers": ["ID", "Nome", "Nascimento", "Livro"],
        "keys": ["ID_AUTOR", "NOME", "DATA_NASCI", "LIVRO"],
        "search": "A.NOME LIKE %s OR L.TITULO LIKE %s",
    },
    "alunos": {
        "table": "ALUNOS", "pk": "ID_ALUNO",
        "fields": [
            ("nome", "NOME", "Nome", "text", True),
            ("cpf", "CPF_ALUN", "CPF", "text", True),
            ("matr", "MATR", "Matrícula", "number", False),
        ],
        "select": "SELECT ID_ALUNO,NOME,CPF_ALUN,MATR FROM ALUNOS ORDER BY NOME",
        "headers": ["ID", "Nome", "CPF", "Matrícula"],
        "keys": ["ID_ALUNO", "NOME", "CPF_ALUN", "MATR"],
        "search": "NOME LIKE %s OR CPF_ALUN LIKE %s",
    },
}


def safe_select(entity, search_term):
    cfg = CONFIG[entity]
    if search_term:
        if entity == "autores":
            sql = """SELECT A.ID_AUTOR,A.NOME,A.DATA_NASCI,A.ID_LIVRO,L.TITULO AS LIVRO
                     FROM AUTORES A LEFT JOIN LIVROS L ON L.ID_LIVRO=A.ID_LIVRO
                     WHERE A.NOME LIKE %s OR L.TITULO LIKE %s ORDER BY A.NOME"""
        elif entity == "livros":
            sql = """SELECT ID_LIVRO,TITULO,GENERO,`PREÇO` AS PRECO,CAPA_URL
                     FROM LIVROS WHERE TITULO LIKE %s OR GENERO LIKE %s ORDER BY TITULO"""
        else:
            sql = """SELECT ID_ALUNO,NOME,CPF_ALUN,MATR FROM ALUNOS
                     WHERE NOME LIKE %s OR CPF_ALUN LIKE %s ORDER BY NOME"""
        term = f"%{search_term}%"
        return query(sql, (term, term))
    return query(cfg["select"])


def crud(entity):
    cfg = CONFIG[entity]
    if request.method == "POST":
        action = request.form.get("action", "create")
        values = []
        for key, column, label, field_type, required_field in cfg["fields"]:
            value = request.form.get(key, "").strip()
            if value == "" and not required_field:
                value = None
            if key in ("preco", "matr", "id_livro") and value is not None:
                value = float(value) if key == "preco" else int(value)
            values.append(value)
        try:
            columns = [f[1] for f in cfg["fields"]]
            quoted_columns = [f"`{c}`" if c == "PREÇO" else c for c in columns]
            if action == "update":
                sets = ", ".join(f"{col}=%s" for col in quoted_columns)
                change(f"UPDATE {cfg['table']} SET {sets} WHERE {cfg['pk']}=%s",
                       tuple(values + [int(request.form["id"])]))
                flash("Alterações salvas.", "sucesso")
            else:
                marks = ", ".join(["%s"] * len(values))
                change(f"INSERT INTO {cfg['table']} ({', '.join(quoted_columns)}) VALUES ({marks})", tuple(values))
                flash("Cadastro realizado.", "sucesso")
        except (Error, ValueError, KeyError) as exc:
            flash(f"Não foi possível salvar o registro: {exc}", "erro")
        return redirect(url_for(entity))

    term = request.args.get("q", "").strip()
    edit = None
    try:
        rows = safe_select(entity, term)
        edit_id = request.args.get("edit", type=int)
        if edit_id:
            edit = next((row for row in rows if row[cfg["pk"]] == edit_id), None)
            if edit is None:
                all_rows = safe_select(entity, "")
                edit = next((row for row in all_rows if row[cfg["pk"]] == edit_id), None)
    except Error as exc:
        rows = []
        flash(f"Erro ao consultar os registros: {exc}. Confira se executou a migração SQL.", "erro")
    return render_template("crud.html", title={"livros": "Livros", "autores": "Autores", "alunos": "Alunos"}[entity],
                           page=entity, entity=entity, cfg=cfg, rows=rows, edit=edit, search_term=term)


@app.route("/livros", methods=["GET", "POST"])
@required
def livros():
    return crud("livros")


@app.route("/autores", methods=["GET", "POST"])
@required
def autores():
    return crud("autores")


@app.route("/alunos", methods=["GET", "POST"])
@required
def alunos():
    return crud("alunos")


@app.route("/<entity>/excluir/<int:record_id>", methods=["POST"])
@required
def delete_record(entity, record_id):
    if entity not in CONFIG:
        return redirect(url_for("inicio"))
    cfg = CONFIG[entity]
    try:
        if entity == "livros" and query("SELECT ID_EMPRESTIMO FROM EMPRESTIMO WHERE ID_LIVRO=%s LIMIT 1", (record_id,)):
            flash("Este livro possui histórico de empréstimos e não pode ser excluído.", "erro")
            return redirect(url_for(entity))
        if entity == "alunos" and query("SELECT ID_EMPRESTIMO FROM EMPRESTIMO WHERE ID_ALUNO=%s LIMIT 1", (record_id,)):
            flash("Este aluno possui histórico de empréstimos. O cadastro foi mantido.", "erro")
            return redirect(url_for(entity))
        change(f"DELETE FROM {cfg['table']} WHERE {cfg['pk']}=%s", (record_id,))
        flash("Registro excluído.", "sucesso")
    except Error as exc:
        flash(f"Não foi possível excluir: {exc}", "erro")
    return redirect(url_for(entity))


@app.route("/emprestimos", methods=["GET", "POST"])
@required
def emprestimos():
    if request.method == "POST":
        try:
            student_id = int(request.form["id_aluno"])
            book_id = int(request.form["id_livro"])
            value = float(request.form.get("valor") or 0)
            loan_date = request.form.get("data") or date.today().isoformat()
            if not query("SELECT ID_ALUNO FROM ALUNOS WHERE ID_ALUNO=%s", (student_id,)):
                flash("Aluno não encontrado.", "erro")
            elif not query("SELECT ID_LIVRO FROM LIVROS WHERE ID_LIVRO=%s", (book_id,)):
                flash("Livro não encontrado.", "erro")
            elif query("SELECT ID_EMPRESTIMO FROM EMPRESTIMO WHERE ID_LIVRO=%s AND STATUS='Emprestado'", (book_id,)):
                flash("Este livro já está emprestado.", "erro")
            else:
                change("""INSERT INTO EMPRESTIMO (VALOR,DATA_EMPREST,ID_LIVRO,ID_ALUNO,STATUS)
                          VALUES (%s,%s,%s,%s,'Emprestado')""", (value, loan_date, book_id, student_id))
                flash("Empréstimo registrado.", "sucesso")
        except (Error, ValueError, KeyError) as exc:
            flash(f"Erro ao registrar empréstimo: {exc}", "erro")
        return redirect(url_for("emprestimos"))

    term = request.args.get("q", "").strip()
    students, books, rows = [], [], []
    try:
        students = query("SELECT ID_ALUNO,NOME FROM ALUNOS ORDER BY NOME")
        books = query("""SELECT L.ID_LIVRO,L.TITULO FROM LIVROS L
                         WHERE NOT EXISTS (SELECT 1 FROM EMPRESTIMO E WHERE E.ID_LIVRO=L.ID_LIVRO
                         AND E.STATUS='Emprestado') ORDER BY L.TITULO""")
       
        rows = query("""
    SELECT
              E.ID_EMPRESTIMO,
             E.DATA_EMPREST,
             E.STATUS,
             E.VALOR,
             A.NOME AS ALUNO,
             L.TITULO AS LIVRO
                FROM EMPRESTIMO E
                JOIN ALUNOS A ON A.ID_ALUNO = E.ID_ALUNO
                JOIN LIVROS L ON L.ID_LIVRO = E.ID_LIVRO
                WHERE A.NOME LIKE %s OR L.TITULO LIKE %s
                ORDER BY E.ID_EMPRESTIMO DESC
            """, (f"%{term}%", f"%{term}%"))

    except Error as exc:
        flash(f"Erro ao consultar empréstimos: {exc}", "erro")
    return render_template("emprestimos.html", title="Empréstimos", page="emprestimos",
                           students=students, books=books, rows=rows, today=date.today().isoformat(), search_term=term)


@app.route("/devolucoes", methods=["GET", "POST"])
@required
def devolucoes():
    if request.method == "POST":
        try:
            loan_id = int(request.form["id_emprestimo"])
            return_date = request.form.get("data") or date.today().isoformat()
            _, changed = change("""UPDATE EMPRESTIMO SET STATUS='Devolvido', DATA_DEVOLUCAO=%s
                                  WHERE ID_EMPRESTIMO=%s AND STATUS='Emprestado'""", (return_date, loan_id))
            flash("Devolução registrada. O livro está disponível novamente." if changed else
                  "Empréstimo não encontrado ou já devolvido.", "sucesso" if changed else "erro")
        except (Error, ValueError, KeyError) as exc:
            flash(f"Erro ao registrar devolução: {exc}", "erro")
        return redirect(url_for("devolucoes"))
    try:
        
        rows = query("""
 SELECT
        E.ID_EMPRESTIMO,
        E.DATA_EMPREST,
        A.NOME AS ALUNO,
        L.TITULO AS LIVRO
    FROM EMPRESTIMO E
    JOIN ALUNOS A
        ON A.ID_ALUNO = E.ID_ALUNO
    JOIN LIVROS L
        ON L.ID_LIVRO = E.ID_LIVRO
    WHERE E.STATUS = 'Emprestado'
    ORDER BY E.ID_EMPRESTIMO DESC
""")

    except Error as exc:
        rows = []
        flash(f"Erro ao consultar devoluções: {exc}", "erro")
    return render_template("devolucoes.html", title="Devoluções", page="devolucoes",
                           rows=rows, today=date.today().isoformat())


@app.route("/historico")
@required
def historico():
    term = request.args.get("q", "").strip()
    try:
        rows = query("""SELECT E.ID_EMPRESTIMO,E.DATA_EMPREST,E.DATA_DEVOLUCAO,E.STATUS,E.VALOR,
                        A.NOME ALUNO,L.TITULO LIVRO FROM EMPRESTIMO E
                        JOIN ALUNOS A ON A.ID_ALUNO=E.ID_ALUNO
                        JOIN LIVROS L ON L.ID_LIVRO=E.ID_LIVRO
                        WHERE A.NOME LIKE %s OR L.TITULO LIKE %s OR E.STATUS LIKE %s
                        ORDER BY E.ID_EMPRESTIMO DESC""", (f"%{term}%", f"%{term}%", f"%{term}%"))
    except Error as exc:
        rows = []
        flash(f"Erro ao consultar histórico: {exc}", "erro")
    return render_template("historico.html", title="Histórico", page="historico", rows=rows, search_term=term)


if __name__ == "__main__":
    app.run(debug=True)
