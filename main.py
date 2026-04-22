import pymysql
import re
import base64
import hashlib
import hmac
import secrets
from mangum import Mangum
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime

def validate_email(email: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))

def validate_cpf(cpf: str) -> bool:
    return bool(re.match(r"^\d{3}\.?\d{3}\.?\d{3}-?\d{2}$", cpf))

def validate_phone(phone: str) -> bool:
    return bool(re.match(r"^\(?\d{2}\)?\s?9?\d{4}-?\d{4}$", phone))

def validate_password(password: str) -> bool:
    return bool(re.match(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$", password))

def validate_drt(drt: str) -> bool:
    return bool(re.match(r"^DRT-\d+$", drt))

def validate_name(name: str) -> bool:
    return bool(re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s']+$", name))

app = FastAPI()

# Configuração de sessão
app.add_middleware(
    SessionMiddleware,
    secret_key="grip_secret",
    session_cookie="grip_session",
    max_age=3600,
    same_site="lax",
    https_only=True
)

# Arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/templates/styles", StaticFiles(directory="templates/styles"), name="styles")
app.mount("/templates/script", StaticFiles(directory="templates/script"), name="scripts")
templates = Jinja2Templates(directory="templates")

# Banco de dados
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "dudumysql",
    "database": "grip"
}

PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 390000


def get_db():
    return pymysql.connect(**DB_CONFIG)

def verify_logged_in(request: Request):
    if not request.session.get("user_logged_in"):
        raise HTTPException(status_code=303, headers={"Location": "/login"})

def verify_admin(request: Request):
    if not request.session.get("user_logged_in"):
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    if request.session.get("perfil") != "admin":
        raise HTTPException(status_code=303, headers={"Location": "/aulaListar"})

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS
    )
    encoded_hash = base64.b64encode(password_hash).decode("utf-8")
    return f"{PASSWORD_ALGORITHM}${PASSWORD_ITERATIONS}${salt}${encoded_hash}"


def is_password_hashed(stored_password: str) -> bool:
    return stored_password.startswith(f"{PASSWORD_ALGORITHM}$")


def verify_password(plain_password: str, stored_password: str) -> bool:
    if not stored_password:
        return False
    if is_password_hashed(stored_password):
        try:
            algorithm, iterations, salt, password_hash = stored_password.split("$", 3)
            if algorithm != PASSWORD_ALGORITHM:
                return False
            derived_hash = hashlib.pbkdf2_hmac(
                "sha256",
                plain_password.encode("utf-8"),
                salt.encode("utf-8"),
                int(iterations)
            )
            encoded_derived_hash = base64.b64encode(derived_hash).decode("utf-8")
            return hmac.compare_digest(encoded_derived_hash, password_hash)
        except (ValueError, TypeError):
            return False
    return hmac.compare_digest(plain_password, stored_password)


# ── Páginas públicas ──────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario")
    })

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    if request.session.get("user_logged_in"):
        if request.session.get("perfil") == "admin":
            return RedirectResponse(url="/profPerfil", status_code=303)
        return RedirectResponse(url="/alunoPerfil", status_code=303)
    
    login_error = request.session.pop("login_error", None)
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "login_error": login_error
    })

@app.get("/aulas", response_class=HTMLResponse)
async def aulas_page(request: Request):
    return templates.TemplateResponse("aulas.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario")
    })


@app.get("/professores", response_class=HTMLResponse)
async def professores_page(request: Request):
    return templates.TemplateResponse("professores.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario")
    })


@app.get("/planos", response_class=HTMLResponse)
async def planos_page(request: Request):
    return templates.TemplateResponse("planos.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario")
    })


@app.get("/sobre", response_class=HTMLResponse)
async def sobre_page(request: Request):
    return templates.TemplateResponse("sobre.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario")
    })


@app.get("/professor-perfil", response_class=HTMLResponse)
async def professor_perfil(request: Request):
    return templates.TemplateResponse("professor-perfil.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario")
    })


# ── Autenticação ──────────────────────────────────────────────────────────────

@app.post("/login")
async def login(
    request: Request,
    Email: str = Form(...),
    Senha: str = Form(...),
    db=Depends(get_db)
):
    if not validate_email(Email):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "E-mail inválido"
        })
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, senha FROM Professor WHERE email = %s", (Email,))
            professor = cursor.fetchone()
            
            if professor and verify_password(Senha, professor["senha"]):
                request.session["user_logged_in"] = True
                request.session["usuario_id"] = professor["id"]
                request.session["nome_usuario"] = professor["nome"]
                request.session["perfil"] = "admin"
                return RedirectResponse(url="/profPerfil", status_code=303)

            cursor.execute("SELECT id, nome, senha FROM Aluno WHERE email = %s", (Email,))
            aluno = cursor.fetchone()

            if aluno and verify_password(Senha, aluno["senha"]):
                request.session["user_logged_in"] = True
                request.session["usuario_id"] = aluno["id"]
                request.session["nome_usuario"] = aluno["nome"]
                request.session["email_usuario"] = Email
                request.session["perfil"] = "user"
                return RedirectResponse(url="/alunoPerfil", status_code=303)

            request.session["login_error"] = "E-mail ou senha incorretos."
            request.session["show_login_modal"] = True
            return RedirectResponse(url="/login", status_code=303)
    finally:
        db.close()

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@app.get("/logado")
async def usuario_logado(request: Request):
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/login", status_code=303)
    if request.session.get("perfil") == "admin":
        return RedirectResponse(url="/profPerfil", status_code=303)
    return RedirectResponse(url="/alunoPerfil", status_code=303)


@app.get("/alunoPerfil", response_class=HTMLResponse)
async def aluno_perfil(request: Request, db=Depends(get_db)):
    if not request.session.get("user_logged_in"):
        return RedirectResponse(url="/login", status_code=303)
    usuario_id = request.session.get("usuario_id")
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, cpf, telefone, email FROM Aluno WHERE id = %s", (usuario_id,))
            aluno = cursor.fetchone()
    finally:
        db.close()
    return templates.TemplateResponse("alunoPerfil.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario"),
        "aluno": aluno,
    })


@app.get("/profPerfil", response_class=HTMLResponse)
async def prof_perfil(request: Request, db=Depends(get_db)):
    if not request.session.get("user_logged_in") or request.session.get("perfil") != "admin":
        return RedirectResponse(url="/login", status_code=303)
    usuario_id = request.session.get("usuario_id")
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, registro_drt, cpf, email FROM Professor WHERE id = %s", (usuario_id,))
            professor = cursor.fetchone()
            cursor.execute("SELECT id, nome, cpf, telefone, email FROM Aluno ORDER BY nome")
            alunos = cursor.fetchall()
            cursor.execute("SELECT id, nome, registro_drt, cpf, email FROM Professor ORDER BY nome")
            professores = cursor.fetchall()
            cursor.execute("""
                SELECT A.id, A.nome, A.data, A.descricao, P.nome AS professor_nome
                FROM Aula A
                LEFT JOIN Professor P ON A.fk_Professor_id = P.id
                ORDER BY A.data DESC
            """)
            aulas = cursor.fetchall()
    finally:
        db.close()

    for aula in aulas:
        if aula["data"]:
            d = aula["data"]
            aula["data_fmt"] = d.strftime("%d/%m/%Y") if hasattr(d, "strftime") else str(d)
        else:
            aula["data_fmt"] = "-"

    mensagem = request.session.pop("mensagem", None)

    return templates.TemplateResponse("profPerfil.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario"),
        "perfil": request.session.get("perfil"),
        "professor": professor,
        "alunos": alunos,
        "professores": professores,
        "aulas": aulas,
        "total_alunos": len(alunos),
        "total_professores": len(professores),
        "total_aulas": len(aulas),
        "mensagem": mensagem,
    })


@app.get("/cadastro", response_class=HTMLResponse)
async def cadastro_page(request: Request):
    mensagem = request.session.pop("mensagem", None)
    return templates.TemplateResponse("cadastro.html", {
        "request": request,
        "mensagem": mensagem
    })


@app.post("/cadastro")
async def cadastrar_usuario(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    confirmar_senha: str = Form(None),
    cpf: str = Form(""),
    telefone: str = Form(""),
    db=Depends(get_db)
):
    if not validate_name(nome) or not validate_email(email) or not validate_cpf(cpf) or not validate_phone(telefone) or not validate_password(senha):
        return templates.TemplateResponse("cadastro.html", {
            "request": request,
            "error": "Dados inválidos ou formato de nome/e-mail/cpf/telefone/senha incorreto"
        })

    if senha != confirmar_senha:
        request.session["mensagem"] = "Erro: As senhas não coincidem!"
        return RedirectResponse(url="/cadastro", status_code=303)

    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM Aluno WHERE email = %s", (email,))
            if cursor.fetchone():
                request.session["mensagem"] = "Erro: Este e-mail já está em uso!"
                return RedirectResponse(url="/cadastro", status_code=303)

            senha_hash = hash_password(senha)
            cursor.execute(
                "INSERT INTO Aluno (nome, cpf, telefone, email, senha) VALUES (%s, %s, %s, %s, %s)",
                (nome, cpf, telefone, email, senha_hash)
            )
            db.commit()
            request.session["mensagem"] = "Aluno cadastrado com sucesso! Você já pode realizar login."
            return RedirectResponse(url="/cadastro", status_code=303)
    except Exception as e:
        request.session["mensagem"] = f"Erro ao cadastrar: {str(e)}"
        return RedirectResponse(url="/cadastro", status_code=303)
    finally:
        db.close()

# ── Professor CRUD ────────────────────────────────────────────────────────────

@app.get("/profListar", response_class=HTMLResponse)
async def listar_professores(request: Request, db=Depends(get_db)):
    if not request.session.get("user_logged_in") or request.session.get("perfil") != "admin":
        return RedirectResponse(url="/aulaListar", status_code=303)
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, registro_drt, cpf, email FROM Professor ORDER BY nome")
            professores = cursor.fetchall()
    finally:
        db.close()
    mensagem = request.session.pop("mensagem", None)
    return templates.TemplateResponse("profListar.html", {
        "request": request,
        "professores": professores,
        "hoje": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "nome_usuario": request.session.get("nome_usuario"),
        "perfil": request.session.get("perfil"),
        "mensagem": mensagem
    })

@app.get("/profIncluir", response_class=HTMLResponse)
async def prof_incluir(request: Request, auth=Depends(verify_admin)):
    return templates.TemplateResponse("profIncluir.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario")
    })

@app.post("/profIncluir")
async def prof_incluir_post(
    request: Request,
    nome: str = Form(...),
    registro_drt: str = Form(...),
    cpf: str = Form(""),
    email: str = Form(...),
    senha: str = Form(...),
    db=Depends(get_db),
    auth=Depends(verify_admin)
):
    if not validate_email(email) or not validate_drt(registro_drt) or not validate_name(nome):
        request.session["mensagem"] = "Dados inválidos (Nome, E-mail ou DRT)"
        return RedirectResponse(url="/profListar", status_code=303)
    try:
        with db.cursor() as cursor:
            senha_hash = hash_password(senha)
            cursor.execute(
                "INSERT INTO Professor (nome, registro_drt, cpf, email, senha) VALUES (%s, %s, %s, %s, %s)",
                (nome, registro_drt, cpf, email, senha_hash)
            )
            db.commit()
        request.session["mensagem"] = "Professor cadastrado com sucesso!"
    except Exception as e:
        request.session["mensagem"] = f"Erro ao cadastrar: {str(e)}"
    finally:
        db.close()
    return RedirectResponse(url="/profListar", status_code=303)

@app.get("/profExcluir", response_class=HTMLResponse)
async def prof_excluir(request: Request, id: int, db=Depends(get_db), auth=Depends(verify_admin)):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, registro_drt, cpf, email FROM Professor WHERE id = %s", (id,))
            professor = cursor.fetchone()
    finally:
        db.close()
    return templates.TemplateResponse("profExcluir.html", {
        "request": request,
        "prof": professor,
        "nome_usuario": request.session.get("nome_usuario")
    })

@app.post("/profExcluir")
async def prof_excluir_post(request: Request, id: int = Form(...), db=Depends(get_db), auth=Depends(verify_admin)):
    try:
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM Professor WHERE id = %s", (id,))
            db.commit()
        request.session["mensagem"] = "Professor excluído com sucesso."
    except Exception as e:
        request.session["mensagem"] = f"Erro ao excluir: {str(e)}"
    finally:
        db.close()
    return RedirectResponse(url="/profListar", status_code=303)

@app.get("/profAtualizar", response_class=HTMLResponse)
async def prof_atualizar(request: Request, id: int, db=Depends(get_db), auth=Depends(verify_admin)):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, registro_drt, cpf, email FROM Professor WHERE id = %s", (id,))
            professor = cursor.fetchone()
    finally:
        db.close()
    return templates.TemplateResponse("profAtualizar.html", {
        "request": request,
        "prof": professor,
        "nome_usuario": request.session.get("nome_usuario")
    })

@app.post("/profAtualizar")
async def prof_atualizar_post(
    request: Request,
    id: int = Form(...),
    nome: str = Form(...),
    email: str = Form(...),
    db=Depends(get_db),
    auth=Depends(verify_admin)
):
    try:
        with db.cursor() as cursor:
            cursor.execute("UPDATE Professor SET nome=%s, email=%s WHERE id=%s", (nome, email, id))
            db.commit()
        request.session["mensagem"] = "Cadastro do professor atualizado com sucesso!"
    except Exception as e:
        request.session["mensagem"] = f"Erro ao atualizar: {str(e)}"
    finally:
        db.close()
    return RedirectResponse(url="/profListar", status_code=303)

@app.get("/profSenha", response_class=HTMLResponse)
async def prof_senha(request: Request, id: int, db=Depends(get_db), auth=Depends(verify_admin)):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome FROM Professor WHERE id = %s", (id,))
            professor = cursor.fetchone()
    finally:
        db.close()
    return templates.TemplateResponse("profSenha.html", {
        "request": request,
        "prof": professor,
        "nome_usuario": request.session.get("nome_usuario")
    })

@app.post("/profSenha")
async def prof_senha_post(
    request: Request,
    id: int = Form(...),
    nova_senha: str = Form(...),
    db=Depends(get_db),
    auth=Depends(verify_admin)
):
    try:
        with db.cursor() as cursor:
            senha_hash = hash_password(nova_senha)
            cursor.execute("UPDATE Professor SET senha=%s WHERE id=%s", (senha_hash, id))
            db.commit()
        request.session["mensagem"] = "Senha do professor atualizada com sucesso!"
    except Exception as e:
        request.session["mensagem"] = f"Erro ao atualizar senha: {str(e)}"
    finally:
        db.close()
    return RedirectResponse(url="/profListar", status_code=303)

# ── Aluno CRUD ────────────────────────────────────────────────────────────────

@app.get("/alunoListar", response_class=HTMLResponse)
async def listar_alunos(request: Request, db=Depends(get_db), auth=Depends(verify_logged_in)):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, cpf, telefone, email FROM Aluno ORDER BY nome")
            alunos = cursor.fetchall()
    finally:
        db.close()
    mensagem = request.session.pop("mensagem", None)
    return templates.TemplateResponse("alunoListar.html", {
        "request": request,
        "alunos": alunos,
        "hoje": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "nome_usuario": request.session.get("nome_usuario"),
        "perfil": request.session.get("perfil"),
        "mensagem": mensagem
    })

@app.get("/alunoIncluir", response_class=HTMLResponse)
async def aluno_incluir(request: Request, auth=Depends(verify_admin)):
    return templates.TemplateResponse("alunoIncluir.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario")
    })

@app.post("/alunoIncluir")
async def aluno_incluir_post(
    request: Request,
    nome: str = Form(...),
    cpf: str = Form(""),
    telefone: str = Form(""),
    email: str = Form(...),
    senha: str = Form(...),
    db=Depends(get_db),
    auth=Depends(verify_admin)
):
    try:
        with db.cursor() as cursor:
            senha_hash = hash_password(senha)
            cursor.execute(
                "INSERT INTO Aluno (nome, cpf, telefone, email, senha) VALUES (%s, %s, %s, %s, %s)",
                (nome, cpf, telefone, email, senha_hash)
            )
            db.commit()
        request.session["mensagem"] = "Aluno cadastrado com sucesso!"
    except Exception as e:
        request.session["mensagem"] = f"Erro ao cadastrar: {str(e)}"
    finally:
        db.close()
    return RedirectResponse(url="/alunoListar", status_code=303)

@app.get("/alunoExcluir", response_class=HTMLResponse)
async def aluno_excluir(request: Request, id: int, db=Depends(get_db), auth=Depends(verify_admin)):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, cpf, telefone, email FROM Aluno WHERE id = %s", (id,))
            aluno = cursor.fetchone()
    finally:
        db.close()
    return templates.TemplateResponse("alunoExcluir.html", {
        "request": request,
        "aluno": aluno,
        "nome_usuario": request.session.get("nome_usuario")
    })

@app.post("/alunoExcluir")
async def aluno_excluir_post(request: Request, id: int = Form(...), db=Depends(get_db), auth=Depends(verify_admin)):
    try:
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM Aluno WHERE id = %s", (id,))
            db.commit()
        request.session["mensagem"] = "Aluno excluído com sucesso."
    except Exception as e:
        request.session["mensagem"] = f"Erro ao excluir: {str(e)}"
    finally:
        db.close()
    return RedirectResponse(url="/alunoListar", status_code=303)

@app.get("/alunoAtualizar", response_class=HTMLResponse)
async def aluno_atualizar(request: Request, id: int, db=Depends(get_db), auth=Depends(verify_admin)):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, cpf, telefone, email FROM Aluno WHERE id = %s", (id,))
            aluno = cursor.fetchone()
    finally:
        db.close()
    return templates.TemplateResponse("alunoAtualizar.html", {
        "request": request,
        "aluno": aluno,
        "nome_usuario": request.session.get("nome_usuario")
    })

@app.post("/alunoAtualizar")
async def aluno_atualizar_post(
    request: Request,
    id: int = Form(...),
    nome: str = Form(...),
    telefone: str = Form(""),
    email: str = Form(...),
    db=Depends(get_db),
    auth=Depends(verify_admin)
):
    try:
        with db.cursor() as cursor:
            cursor.execute("UPDATE Aluno SET nome=%s, telefone=%s, email=%s WHERE id=%s", (nome, telefone, email, id))
            db.commit()
        request.session["mensagem"] = "Cadastro do aluno atualizado com sucesso!"
    except Exception as e:
        request.session["mensagem"] = f"Erro ao atualizar: {str(e)}"
    finally:
        db.close()
    return RedirectResponse(url="/alunoListar", status_code=303)

@app.get("/alunoSenha", response_class=HTMLResponse)
async def aluno_senha(request: Request, id: int, db=Depends(get_db), auth=Depends(verify_admin)):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome FROM Aluno WHERE id = %s", (id,))
            aluno = cursor.fetchone()
    finally:
        db.close()
    return templates.TemplateResponse("alunoSenha.html", {
        "request": request,
        "aluno": aluno,
        "nome_usuario": request.session.get("nome_usuario")
    })

@app.post("/alunoSenha")
async def aluno_senha_post(
    request: Request,
    id: int = Form(...),
    nova_senha: str = Form(...),
    db=Depends(get_db),
    auth=Depends(verify_admin)
):
    if not validate_password(nova_senha):
        request.session["mensagem"] = "Erro: Senha muito fraca"
        return RedirectResponse(url="/alunoListar", status_code=303)
    try:
        with db.cursor() as cursor:
            senha_hash = hash_password(nova_senha)
            cursor.execute("UPDATE Aluno SET senha=%s WHERE id=%s", (senha_hash, id))
            db.commit()
        request.session["mensagem"] = "Senha do aluno atualizada com sucesso!"
    except Exception as e:
        request.session["mensagem"] = f"Erro ao atualizar senha: {str(e)}"
    finally:
        db.close()
    return RedirectResponse(url="/alunoListar", status_code=303)

# ── Aula CRUD ────────────────────────────────────────────────────────────────

@app.get("/aulaListar", response_class=HTMLResponse)
async def listar_aulas(request: Request, db=Depends(get_db), auth=Depends(verify_logged_in)):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT A.id, A.nome, A.data, A.descricao, P.nome AS professor_nome
                FROM Aula A
                LEFT JOIN Professor P ON A.fk_Professor_id = P.id
                ORDER BY A.data DESC
            """)
            aulas = cursor.fetchall()
    finally:
        db.close()
    for aula in aulas:
        if aula["data"]:
            d = aula["data"]
            aula["data_fmt"] = d.strftime("%d/%m/%Y") if hasattr(d, "strftime") else str(d)
        else:
            aula["data_fmt"] = "-"
    mensagem = request.session.pop("mensagem", None)
    return templates.TemplateResponse("aulaListar.html", {
        "request": request,
        "aulas": aulas,
        "hoje": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "nome_usuario": request.session.get("nome_usuario"),
        "perfil": request.session.get("perfil"),
        "mensagem": mensagem
    })

@app.get("/aulaIncluir", response_class=HTMLResponse)
async def aula_incluir(request: Request, db=Depends(get_db), auth=Depends(verify_admin)):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome FROM Professor ORDER BY nome")
            professores = cursor.fetchall()
    finally:
        db.close()
    return templates.TemplateResponse("aulaIncluir.html", {
        "request": request,
        "professores": professores,
        "nome_usuario": request.session.get("nome_usuario")
    })

@app.post("/aulaIncluir")
async def aula_incluir_post(
    request: Request,
    nome: str = Form(...),
    data: str = Form(...),
    descricao: str = Form(""),
    fk_Professor_id: int = Form(...),
    db=Depends(get_db),
    auth=Depends(verify_admin)
):
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO Aula (nome, data, descricao, fk_Professor_id) VALUES (%s, %s, %s, %s)",
                (nome, data, descricao, fk_Professor_id)
            )
            db.commit()
        request.session["mensagem"] = "Aula cadastrada com sucesso!"
    except Exception as e:
        request.session["mensagem"] = f"Erro ao cadastrar: {str(e)}"
    finally:
        db.close()
    return RedirectResponse(url="/aulaListar", status_code=303)

@app.get("/aulaExcluir", response_class=HTMLResponse)
async def aula_excluir(request: Request, id: int, db=Depends(get_db), auth=Depends(verify_admin)):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT A.id, A.nome, A.data, A.descricao, P.nome AS professor_nome
                FROM Aula A
                LEFT JOIN Professor P ON A.fk_Professor_id = P.id
                WHERE A.id = %s
            """, (id,))
            aula = cursor.fetchone()
    finally:
        db.close()
    return templates.TemplateResponse("aulaExcluir.html", {
        "request": request,
        "aula": aula,
        "nome_usuario": request.session.get("nome_usuario")
    })

@app.post("/aulaExcluir")
async def aula_excluir_post(request: Request, id: int = Form(...), db=Depends(get_db), auth=Depends(verify_admin)):
    try:
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM Aula WHERE id = %s", (id,))
            db.commit()
        request.session["mensagem"] = "Aula excluída com sucesso."
    except Exception as e:
        request.session["mensagem"] = f"Erro ao excluir: {str(e)}"
    finally:
        db.close()
    return RedirectResponse(url="/aulaListar", status_code=303)

@app.get("/aulaAtualizar", response_class=HTMLResponse)
async def aula_atualizar(request: Request, id: int, db=Depends(get_db), auth=Depends(verify_admin)):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, data, descricao, fk_Professor_id FROM Aula WHERE id = %s", (id,))
            aula = cursor.fetchone()
            cursor.execute("SELECT id, nome FROM Professor ORDER BY nome")
            professores = cursor.fetchall()
    finally:
        db.close()
    if aula and aula["data"]:
        d = aula["data"]
        aula["data_fmt"] = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
    return templates.TemplateResponse("aulaAtualizar.html", {
        "request": request,
        "aula": aula,
        "professores": professores,
        "nome_usuario": request.session.get("nome_usuario")
    })

@app.post("/aulaAtualizar")
async def aula_atualizar_post(
    request: Request,
    id: int = Form(...),
    nome: str = Form(...),
    data: str = Form(...),
    descricao: str = Form(""),
    fk_Professor_id: int = Form(...),
    db=Depends(get_db),
    auth=Depends(verify_admin)
):
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE Aula SET nome=%s, data=%s, descricao=%s, fk_Professor_id=%s WHERE id=%s",
                (nome, data, descricao, fk_Professor_id, id)
            )
            db.commit()
        request.session["mensagem"] = "Aula atualizada com sucesso!"
    except Exception as e:
        request.session["mensagem"] = f"Erro ao atualizar: {str(e)}"
    finally:
        db.close()
    return RedirectResponse(url="/aulaListar", status_code=303)
