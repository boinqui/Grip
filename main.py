import pymysql
from mangum import Mangum
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from datetime import date, datetime

app = FastAPI()

# Configuração de sessão
app.add_middleware(
    SessionMiddleware,
    secret_key="grip_secret",
    session_cookie="grip_session",
    max_age=3600,
    same_site="lax",
    https_only=False
)

# Configuração de arquivos estáticos e templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configuração do novo banco de dados
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "12345",  # botar senha do mysql
    "database": "grip"
}

def get_db():
    return pymysql.connect(**DB_CONFIG)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if request.session.get("user_logged_in"):
        return RedirectResponse(url="/profListar", status_code=303)

    login_error = request.session.pop("login_error", None)
    show_login_modal = request.session.pop("show_login_modal", False)
    nome_usuario = request.session.get("nome_usuario", None)

    return templates.TemplateResponse("login.html", {
        "request": request,
        "login_error": login_error,
        "show_login_modal": "block" if show_login_modal else "none",
        "nome_usuario": nome_usuario
    })

@app.post("/login")
async def login(
    request: Request,
    Email: str = Form(...),
    Senha: str = Form(...),
    db = Depends(get_db)
):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # Tenta logar como Professor (Admin)
            cursor.execute("SELECT * FROM Professor WHERE email = %s AND senha = %s", (Email, Senha))
            prof = cursor.fetchone()

            if prof:
                request.session["user_logged_in"] = True
                request.session["nome_usuario"] = prof['nome']
                request.session["perfil"] = "admin"
                return RedirectResponse(url="/profListar", status_code=303)
            
            # Tenta logar como Aluno (Usuário normal)
            cursor.execute("SELECT * FROM Aluno WHERE email = %s AND senha = %s", (Email, Senha))
            aluno = cursor.fetchone()

            if aluno:
                request.session["user_logged_in"] = True
                request.session["nome_usuario"] = aluno['nome']
                request.session["perfil"] = "usuario"
                return RedirectResponse(url="/profListar", status_code=303)

            request.session["login_error"] = "E-mail ou senha inválidos."
            request.session["show_login_modal"] = True
            return RedirectResponse(url="/", status_code=303)
    finally:
        db.close()

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/cadastro", response_class=HTMLResponse)
async def cadastro_page(request: Request):
    mensagem = request.session.pop("mensagem", None)
    return templates.TemplateResponse("cadastro.html", {"request": request, "mensagem": mensagem})

@app.post("/cadastro", name="cadastro")
async def cadastrar_usuario(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    confirmar_senha: str = Form(None),
    cpf: str = Form(""),
    data_nascimento: str = Form("2000-01-01"),
    telefone: str = Form(""),
    db = Depends(get_db)
):
    try:
        # Validação de senha
        if confirmar_senha and senha != confirmar_senha:
            request.session["mensagem"] = "Erro: As senhas não coincidem!"
            return RedirectResponse(url="/cadastro", status_code=303)

        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM Aluno WHERE email = %s", (email,))
            if cursor.fetchone():
                request.session["mensagem"] = "Erro: Este e-mail já está em uso!"
                return RedirectResponse(url="/cadastro", status_code=303)

            # Inserção no banco
            sql = """INSERT INTO Aluno (nome, cpf, data_nascimento, telefone, email, senha) 
                     VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (nome, cpf, data_nascimento, telefone, email, senha))
            db.commit()

            request.session["mensagem"] = "Aluno cadastrado com sucesso! Você já pode realizar login."
            return RedirectResponse(url="/cadastro", status_code=303)

    except Exception as e:
        request.session["mensagem"] = f"Erro ao cadastrar: {str(e)}"
        return RedirectResponse(url="/cadastro", status_code=303)
    finally:
        db.close()

@app.get("/profListar", name="profListar", response_class=HTMLResponse)
async def listar_professores(request: Request, db=Depends(get_db)):
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/", status_code=303)

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        sql = """
            SELECT P.id, P.nome, P.registro_drt, P.cpf, P.email, P.data_nascimento, A.nome AS aula_nome
            FROM Professor P 
            JOIN Aula A ON P.fk_Aula_id = A.id
            ORDER BY P.nome
        """
        cursor.execute(sql)
        professores = cursor.fetchall()

    # Cálculo da idade devolvido para o código
    hoje = date.today()
    for prof in professores:
        dt_nasc = prof["data_nascimento"]
        if dt_nasc:
            if isinstance(dt_nasc, str):
                ano, mes, dia = map(int, dt_nasc.split("-"))
                dt_nasc = date(ano, mes, dia)
            idade = hoje.year - dt_nasc.year
            if (dt_nasc.month, dt_nasc.day) > (hoje.month, hoje.day):
                idade -= 1
            prof["idade"] = idade
        else:
            prof["idade"] = "-"

    nome_usuario = request.session.get("nome_usuario", None)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    return templates.TemplateResponse("profListar.html", {
        "request": request,
        "professores": professores,
        "hoje": agora,
        "nome_usuario": nome_usuario
    })

@app.get("/profIncluir", response_class=HTMLResponse)
async def prof_incluir(request: Request, db=Depends(get_db)):
    if not request.session.get("user_logged_in") or request.session.get("perfil") != "admin":
        return RedirectResponse(url="/profListar", status_code=303)

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT id, nome FROM Aula")
        aulas = cursor.fetchall()
    db.close()

    nome_usuario = request.session.get("nome_usuario", None)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    return templates.TemplateResponse("profIncluir.html", {
        "request": request,
        "aulas": aulas,
        "hoje": agora,
        "nome_usuario": nome_usuario
    })

@app.post("/profIncluir_exe")
async def prof_incluir_exe(
    request: Request,
    nome: str = Form(...),
    registro_drt: str = Form(...),
    cpf: str = Form(...),
    data_nascimento: str = Form(None),
    email: str = Form(...),
    senha: str = Form(...),
    fk_Aula_id: int = Form(...),
    db=Depends(get_db)
):
    if not request.session.get("user_logged_in") or request.session.get("perfil") != "admin":
        return RedirectResponse(url="/profListar", status_code=303)

    try:
        with db.cursor() as cursor:
            # Deixando o MySQL cuidar do ID (Auto Increment)
            sql = """INSERT INTO Professor (nome, registro_drt, cpf, data_nascimento, email, senha, fk_Aula_id)
                     VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (nome, registro_drt, cpf, data_nascimento, email, senha, fk_Aula_id))
            db.commit()

        request.session["mensagem_header"] = "Inclusão de Professor"
        request.session["mensagem"] = "Professor cadastrado com sucesso!"
    except Exception as e:
        request.session["mensagem_header"] = "Erro ao cadastrar"
        request.session["mensagem"] = str(e)
    finally:
        db.close()

    return templates.TemplateResponse("profIncluir_exe.html", {
        "request": request,
        "mensagem_header": request.session.get("mensagem_header", ""),
        "mensagem": request.session.get("mensagem", ""),
        "hoje": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "nome_usuario": request.session.get("nome_usuario", None)
    })

@app.get("/profExcluir", response_class=HTMLResponse)
async def prof_excluir(request: Request, id: int, db=Depends(get_db)):
    if not request.session.get("user_logged_in") or request.session.get("perfil") != "admin":
        return RedirectResponse(url="/profListar", status_code=303)

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        sql = ("SELECT P.id, P.nome, P.registro_drt, P.cpf, P.data_nascimento, A.nome as aula_nome "
               "FROM Professor P JOIN Aula A ON P.fk_Aula_id = A.id "
               "WHERE P.id = %s")
        cursor.execute(sql, (id,))
        professor = cursor.fetchone()
    db.close()

    # Formatar data de nascimento para exibição
    data_formatada = "-"
    if professor and professor["data_nascimento"]:
        data_nasc = professor["data_nascimento"]
        if isinstance(data_nasc, str):
            ano, mes, dia = data_nasc.split("-")
        else:
            ano, mes, dia = data_nasc.year, f"{data_nasc.month:02d}", f"{data_nasc.day:02d}"
        data_formatada = f"{dia}/{mes}/{ano}"

    return templates.TemplateResponse("profExcluir.html", {
        "request": request,
        "prof": professor,
        "data_formatada": data_formatada,
        "hoje": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "nome_usuario": request.session.get("nome_usuario", None)
    })

@app.post("/profExcluir_exe")
async def prof_excluir_exe(request: Request, id: int = Form(...), db=Depends(get_db)):
    if not request.session.get("user_logged_in") or request.session.get("perfil") != "admin":
        return RedirectResponse(url="/profListar", status_code=303)

    try:
        with db.cursor() as cursor:
            sql_delete = "DELETE FROM Professor WHERE id = %s"
            cursor.execute(sql_delete, (id,))
            db.commit()

            request.session["mensagem_header"] = "Exclusão de Professor"
            request.session["mensagem"] = "Professor excluído com sucesso."
    except Exception as e:
        request.session["mensagem_header"] = "Erro ao excluir"
        request.session["mensagem"] = str(e)
    finally:
        db.close()

    return templates.TemplateResponse("profExcluir_exe.html", {
        "request": request,
        "mensagem_header": request.session.get("mensagem_header", ""),
        "mensagem": request.session.get("mensagem", ""),
        "hoje": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "nome_usuario": request.session.get("nome_usuario", None)
    })

@app.get("/profAtualizar", response_class=HTMLResponse)
async def prof_atualizar(request: Request, id: int, db=Depends(get_db)):
    if not request.session.get("user_logged_in") or request.session.get("perfil") != "admin":
        return RedirectResponse(url="/profListar", status_code=303)

    with db.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT * FROM Professor WHERE id = %s", (id,))
        professor = cursor.fetchone()
        cursor.execute("SELECT id, nome FROM Aula")
        aulas = cursor.fetchall()
    db.close()

    return templates.TemplateResponse("profAtualizar.html", {
        "request": request,
        "prof": professor,
        "aulas": aulas,
        "hoje": datetime.now().strftime("%d/%m/%Y %H:%M")
    })

@app.post("/profAtualizar_exe")
async def prof_atualizar_exe(
    request: Request,
    id: int = Form(...),
    nome: str = Form(...),
    registro_drt: str = Form(...),
    cpf: str = Form(...),
    data_nascimento: str = Form(None),
    email: str = Form(...),
    senha: str = Form(...),
    fk_Aula_id: int = Form(...),
    db=Depends(get_db)
):
    if not request.session.get("user_logged_in") or request.session.get("perfil") != "admin":
        return RedirectResponse(url="/profListar", status_code=303)

    try:
        with db.cursor() as cursor:
            sql = """UPDATE Professor 
                     SET nome=%s, registro_drt=%s, cpf=%s, data_nascimento=%s, email=%s, senha=%s, fk_Aula_id=%s
                     WHERE id=%s"""
            cursor.execute(sql, (nome, registro_drt, cpf, data_nascimento, email, senha, fk_Aula_id, id))
            db.commit()

        request.session["mensagem_header"] = "Atualização de Professor"
        request.session["mensagem"] = "Registro atualizado com sucesso!"

    except Exception as e:
        request.session["mensagem_header"] = "Erro ao atualizar"
        request.session["mensagem"] = str(e)
    finally:
        db.close()

    return templates.TemplateResponse("profAtualizar_exe.html", {
        "request": request,
        "mensagem_header": request.session.get("mensagem_header", ""),
        "mensagem": request.session.get("mensagem", ""),
        "hoje": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "nome_usuario": request.session.get("nome_usuario", None)
    })

@app.post("/reset_session")
async def reset_session(request: Request):
    request.session.pop("mensagem_header", None)
    request.session.pop("mensagem", None)
    return {"status": "ok"}

Mangum(app)