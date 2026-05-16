import pymysql
import base64
import hashlib
import hmac
import secrets
from mangum import Mangum
from validators import validate_email, validate_cpf, validate_phone, validate_password, validate_drt, validate_name, validate_birthday
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import UploadFile, File
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime

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

# Arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Banco de dados
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "carlamysql",
    "database": "grip"
}

PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 390000


def get_db():
    return pymysql.connect(**DB_CONFIG)

def verify_logged_in(request: Request):
    if not request.session.get("user_logged_in"):
        #se nao estiver logado, vai para /login
        raise HTTPException(status_code=303, headers={"Location": "/login"})

def verify_admin(request: Request):
    if not request.session.get("user_logged_in"):
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    if request.session.get("perfil") != "admin":
        #se nao for admin, vai para /login
        raise HTTPException(status_code=303, headers={"Location": "/"})

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

def get_user_foto_b64(request: Request, db):
    """Busca a foto de perfil do usuário logado na sessão atual"""
    usuario_id = request.session.get("usuario_id")
    tipo_usuario = request.session.get("perfil")
    
    if not usuario_id:
        return None
        
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            if tipo_usuario == "admin":
                cursor.execute("SELECT fotoPerfil FROM Professor WHERE id = %s", (usuario_id,))
            else:
                cursor.execute("SELECT fotoPerfil FROM Aluno WHERE id = %s", (usuario_id,))
            
            usuario = cursor.fetchone()
            if usuario and usuario.get("fotoPerfil"):
                return base64.b64encode(usuario["fotoPerfil"]).decode("utf-8")
    except Exception:
        pass
    return None


# ── Páginas públicas ──────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db=Depends(get_db)):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario"),
        "foto_b64": get_user_foto_b64(request, db)
    })

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    if request.session.get("user_logged_in"):
        if request.session.get("perfil") == "admin":
            return RedirectResponse(url="/profPerfil", status_code=303)
        return RedirectResponse(url="/alunoPerfil", status_code=303)

    mensagem = request.session.pop("mensagem", None)
    login_error = request.session.pop("login_error", None)
    if not mensagem and login_error:
        mensagem = login_error if login_error.startswith("Erro:") else f"Erro: {login_error}"

    return templates.TemplateResponse("cadastrologin/login.html", {
        "request": request,
        "mensagem": mensagem,
        "status": "erro" if mensagem else None
    })

@app.get("/aulas", response_class=HTMLResponse)
async def aulas_page(request: Request, db=Depends(get_db)):
    return templates.TemplateResponse("aulas/aulas.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario"),
        "foto_b64": get_user_foto_b64(request, db)
    })


@app.get("/professores", response_class=HTMLResponse)
async def professores_page(request: Request, db=Depends(get_db)):
    return templates.TemplateResponse("professores/professores.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario"),
        "foto_b64": get_user_foto_b64(request, db)
    })


@app.get("/planos", response_class=HTMLResponse)
async def planos_page(request: Request, db=Depends(get_db)):
    return templates.TemplateResponse("planos.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario"),
        "foto_b64": get_user_foto_b64(request, db)
    })


@app.get("/sobre", response_class=HTMLResponse)
async def sobre_page(request: Request, db=Depends(get_db)):
    return templates.TemplateResponse("sobre.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario"),
        "foto_b64": get_user_foto_b64(request, db)
    })


# ── Autenticação ──────────────────────────────────────────────────────────────

@app.post("/login")
async def login(
    request: Request,
    Email: str = Form(...),
    senha: str = Form(...),
    db=Depends(get_db)
):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            #Professor = Admin
            cursor.execute("SELECT id, nome, senha FROM Professor WHERE email = %s", (Email,))
            professor = cursor.fetchone()
            
            if professor and verify_password(senha, professor["senha"]):
                request.session["user_logged_in"] = True
                request.session["usuario_id"] = professor["id"]
                request.session["nome_usuario"] = professor["nome"]
                request.session["perfil"] = "admin" # <-- Define Professor como Admin
                return RedirectResponse(url="/profPerfil", status_code=303)

            #Aluno = User
            cursor.execute("SELECT id, nome, senha FROM Aluno WHERE email = %s", (Email,))
            aluno = cursor.fetchone()

            if aluno and verify_password(senha, aluno["senha"]):
                request.session["user_logged_in"] = True
                request.session["usuario_id"] = aluno["id"]
                request.session["nome_usuario"] = aluno["nome"]
                request.session["email_usuario"] = Email
                request.session["perfil"] = "user" # <-- Define Aluno como User
                return RedirectResponse(url="/alunoPerfil", status_code=303)

            if not professor and not aluno:
                request.session["mensagem"] = "Erro: Conta não encontrada."
            else:
                request.session["mensagem"] = "Erro: E-mail ou senha incorretos."
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
async def aluno_perfil(request: Request, db=Depends(get_db), auth=Depends(verify_logged_in)):
    usuario_id = request.session.get("usuario_id")
    aulas = []
    plano_status = "sem_plano"
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, cpf, telefone, email, fotoPerfil, data_nascimento FROM Aluno WHERE id = %s", (usuario_id,))
            aluno = cursor.fetchone()
            cursor.execute("""
                SELECT A.id, A.nome, A.data, A.descricao, P.nome AS professor_nome
                FROM Professor_Aluno PA
                INNER JOIN Aula A ON A.fk_Professor_id = PA.fk_Professor_id
                LEFT JOIN Professor P ON P.id = A.fk_Professor_id
                WHERE PA.fk_Aluno_id = %s AND A.data >= CURDATE()
                ORDER BY A.data ASC, A.id ASC
                LIMIT 6
            """, (usuario_id,))
            aulas = cursor.fetchall()
    finally:
        db.close()

    foto_b64 = None
    if aluno and aluno.get("fotoPerfil"):
        foto_b64 = base64.b64encode(aluno["fotoPerfil"]).decode("utf-8")

    for aula in aulas:
        if aula["data"]:
            d = aula["data"]
            aula["data_fmt"] = d.strftime("%d/%m/%Y") if hasattr(d, "strftime") else str(d)
        else:
            aula["data_fmt"] = "Data não informada"

    return templates.TemplateResponse("alunos/alunoPerfil.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario"),
        "aluno": aluno,
        "aulas": aulas,
        "plano_status": plano_status,
        "foto_b64": foto_b64,
    })


@app.get("/profPerfil", response_class=HTMLResponse)
async def prof_perfil(request: Request, db=Depends(get_db), auth=Depends(verify_admin)):
    usuario_id = request.session.get("usuario_id")
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, registro_drt, cpf, email, fotoPerfil FROM Professor WHERE id = %s", (usuario_id,))
            professor = cursor.fetchone()
            cursor.execute("SELECT id, nome, cpf, telefone, email, data_nascimento FROM Aluno ORDER BY nome")
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

    foto_b64 = None
    if professor and professor.get("fotoPerfil"):
        foto_b64 = base64.b64encode(professor["fotoPerfil"]).decode("utf-8")

    for aula in aulas:
        if aula["data"]:
            d = aula["data"]
            aula["data_fmt"] = d.strftime("%d/%m/%Y") if hasattr(d, "strftime") else str(d)
        else:
            aula["data_fmt"] = "-"

    mensagem = request.session.pop("mensagem", None)

    return templates.TemplateResponse("professores/profPerfil.html", {
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
    return templates.TemplateResponse("cadastrologin/cadastro.html", {
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
    cpf: str = Form(...),
    telefone: str = Form(...),
    data_nascimento: str = Form(...),
    db=Depends(get_db)
):
    try:
        if confirmar_senha and senha != confirmar_senha:
            request.session["mensagem"] = "Erro: As senhas não coincidem!"
            return RedirectResponse(url="/cadastro", status_code=303)
        
        #colocando regex aqui
        if not validate_name(nome):
            request.session["mensagem"] = "Nome inválido"
            return RedirectResponse(url="/cadastro", status_code=303)
        
        if not validate_email(email):
            request.session["mensagem"] = "Email inválido"
            return RedirectResponse(url="/cadastro", status_code=303)
        
        if not validate_password(senha):
            request.session["mensagem"] = "Senha inválida"
            return RedirectResponse(url="/cadastro", status_code=303)
        
        if not validate_cpf(cpf):
            request.session["mensagem"] = "CPF inválido"
            return RedirectResponse(url="/cadastro", status_code=303)

        if not validate_phone(telefone):
            request.session["mensagem"] = "Telefone inválido"
            return RedirectResponse(url="/cadastro", status_code=303)

        if not validate_birthday(data_nascimento):
            request.session["mensagem"] = "Data de Nascimento inválida"
            return RedirectResponse(url="/cadastro", status_code=303)

        #parte do banco
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM Aluno WHERE email = %s", (email,))
            if cursor.fetchone():
                request.session["mensagem"] = "Erro: Este e-mail já está em uso!"
                return RedirectResponse(url="/cadastro", status_code=303)

            senha_hash = hash_password(senha)
            cursor.execute(
                "INSERT INTO Aluno (nome, cpf, telefone, email, senha, data_nascimento) VALUES (%s, %s, %s, %s, %s, %s)",
                (nome, cpf, telefone, email, senha_hash, data_nascimento)
            )
            db.commit()
            request.session["mensagem"] = "Aluno cadastrado com sucesso! Você já pode realizar login."
            return RedirectResponse(url="/login", status_code=303)

    except Exception as e:
        request.session["mensagem"] = f"Erro ao cadastrar: {str(e)}"
        return RedirectResponse(url="/cadastro", status_code=303)
    finally:
        db.close()

@app.post("/profAtualizarFoto")
async def prof_atualizar_foto(
    request: Request,
    id: int = Form(...),
    fotoPerfil: UploadFile = File(None),
    db=Depends(get_db),
    auth=Depends(verify_logged_in)
):
    try:
        if fotoPerfil and fotoPerfil.filename:
            foto_bytes = await fotoPerfil.read()
            with db.cursor() as cursor:
                cursor.execute(
                    "UPDATE Professor SET fotoPerfil=%s WHERE id=%s",
                    (foto_bytes, id)
                )
                db.commit()
            request.session["mensagem"] = "Foto atualizada com sucesso!"
    except Exception as e:
        request.session["mensagem"] = f"Erro ao atualizar: {str(e)}"
    finally:
        db.close()
        
    return RedirectResponse(url="/profPerfil", status_code=303)












# ── Professor CRUD ────────────────────────────────────────────────────────────

@app.get("/profListar", response_class=HTMLResponse)
async def listar_professores(request: Request, db=Depends(get_db), auth=Depends(verify_admin)):    
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, registro_drt, cpf, email FROM Professor ORDER BY nome")
            professores = cursor.fetchall()
    finally:
        db.close()
        
    mensagem = request.session.pop("mensagem", None)
    
    return templates.TemplateResponse("professores/profListar.html", {
        "request": request,
        "professores": professores,
        "hoje": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "nome_usuario": request.session.get("nome_usuario"),
        "perfil": request.session.get("perfil"),
        "mensagem": mensagem
    })


@app.get("/profIncluir", response_class=HTMLResponse)
async def prof_incluir(request: Request, auth=Depends(verify_admin)):
    return templates.TemplateResponse("professores/profIncluir.html", {
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
    try:

        #regex
        if not validate_name(nome):
            request.session["mensagem"] = "Nome inválido"
            return RedirectResponse(url="/profIncluir", status_code=303)
        
        if not validate_email(email):
            request.session["mensagem"] = "Email inválido"
            return RedirectResponse(url="/profIncluir", status_code=303)
        
        if not validate_password(senha):
            request.session["mensagem"] = "Senha inválida"
            return RedirectResponse(url="/profIncluir", status_code=303)
        
        if not validate_drt(registro_drt):
            request.session["mensagem"] = "Registro DRT inválido"
            return RedirectResponse(url="/profIncluir", status_code=303)
        

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
    return RedirectResponse(url="/profPerfil", status_code=303)


@app.get("/profExcluir", response_class=HTMLResponse)
async def prof_excluir(request: Request, id: int, db=Depends(get_db), auth=Depends(verify_admin)):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, registro_drt, cpf, email FROM Professor WHERE id = %s", (id,))
            professor = cursor.fetchone()
    finally:
        db.close()
    return templates.TemplateResponse("professores/profExcluir.html", {
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
    return RedirectResponse(url="/profPerfil", status_code=303)


@app.get("/profAtualizar", response_class=HTMLResponse)
async def prof_atualizar(request: Request, id: int, db=Depends(get_db), auth=Depends(verify_admin)):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, registro_drt, cpf, email FROM Professor WHERE id = %s", (id,))
            professor = cursor.fetchone()
    finally:
        db.close()
    return templates.TemplateResponse("professores/profAtualizar.html", {
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

        if not validate_name(nome):
            request.session["mensagem"] = "Nome inválido"
            return RedirectResponse(url="/profAtualizar", status_code=303)
        
        if not validate_email(email):
            request.session["mensagem"] = "Email inválido"
            return RedirectResponse(url="/profAtualizar", status_code=303)
        

        with db.cursor() as cursor:
            # Não atualizamos registro_drt, cpf e senha aqui
            cursor.execute(
                "UPDATE Professor SET nome=%s, email=%s WHERE id=%s",
                (nome, email, id)
            )
            db.commit()
        request.session["mensagem"] = "Cadastro do professor atualizado com sucesso!"
    except Exception as e:
        request.session["mensagem"] = f"Erro ao atualizar: {str(e)}"
    finally:
        db.close()
    return RedirectResponse(url="/profPerfil", status_code=303)

@app.get("/profSenha", response_class=HTMLResponse)
async def prof_senha(request: Request, id: int, db=Depends(get_db), auth=Depends(verify_admin)):
    try:

        
        

        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome FROM Professor WHERE id = %s", (id,))
            professor = cursor.fetchone()
    finally:
        db.close()
    return templates.TemplateResponse("professores/profSenha.html", {
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
        if not validate_password(nova_senha):
            request.session["mensagem"] = "Senha inválida"
            return RedirectResponse(url=f"/profSenha?id={id}", status_code=303)

        with db.cursor() as cursor:
            senha_hash = hash_password(nova_senha)
            cursor.execute("UPDATE Professor SET senha=%s WHERE id=%s", (senha_hash, id))
            db.commit()
        request.session["mensagem"] = "Senha do professor atualizada com sucesso!"
    except Exception as e:
        request.session["mensagem"] = f"Erro ao atualizar senha: {str(e)}"
    finally:
        db.close()
    return RedirectResponse(url="/profPerfil", status_code=303)












# ── Aluno CRUD ────────────────────────────────────────────────────────────────

@app.get("/alunoListar", response_class=HTMLResponse)
async def listar_alunos(request: Request, db=Depends(get_db), auth=Depends(verify_logged_in)):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, cpf, telefone, email, data_nascimento FROM Aluno ORDER BY nome")
            alunos = cursor.fetchall()
    finally:
        db.close()
        
    mensagem = request.session.pop("mensagem", None)
    
    return templates.TemplateResponse("alunos/alunoListar.html", {
        "request": request,
        "alunos": alunos,
        "hoje": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "nome_usuario": request.session.get("nome_usuario"),
        "perfil": request.session.get("perfil"),
        "mensagem": mensagem
    })


@app.get("/alunoIncluir", response_class=HTMLResponse)
async def aluno_incluir(request: Request, auth=Depends(verify_admin)):
    return templates.TemplateResponse("alunos/alunoIncluir.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario")
    })


@app.post("/alunoIncluir")
async def aluno_incluir_post(
    request: Request,
    nome: str = Form(...),
    cpf: str = Form(...),
    telefone: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    data_nascimento: str = Form(...),
    db=Depends(get_db),
    auth=Depends(verify_admin)
):
    try:

        #regex
        if not validate_name(nome):
            request.session["mensagem"] = "Nome inválido"
            return RedirectResponse(url="/alunoIncluir", status_code=303)
        
        if not validate_email(email):
            request.session["mensagem"] = "Email inválido"
            return RedirectResponse(url="/alunoIncluir", status_code=303)
        
        if not validate_password(senha):
            request.session["mensagem"] = "Senha inválida"
            return RedirectResponse(url="/alunoIncluir", status_code=303)
        
        if not validate_cpf(cpf):
            request.session["mensagem"] = "CPF inválido"
            return RedirectResponse(url="/alunoIncluir", status_code=303)

        if not validate_phone(telefone):
            request.session["mensagem"] = "Telefone inválido"
            return RedirectResponse(url="/alunoIncluir", status_code=303)

        if not validate_birthday(data_nascimento):
            request.session["mensagem"] = "Data de Nascimento inválida"
            return RedirectResponse(url="/alunoIncluir", status_code=303)

        #banco
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
    return RedirectResponse(url="/profPerfil", status_code=303)


@app.get("/alunoExcluir", response_class=HTMLResponse)
async def aluno_excluir(request: Request, id: int, db=Depends(get_db), auth=Depends(verify_admin)):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, cpf, telefone, email, data_nascimento FROM Aluno WHERE id = %s", (id,))
            aluno = cursor.fetchone()
    finally:
        db.close()
    return templates.TemplateResponse("alunos/alunoExcluir.html", {
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
    return RedirectResponse(url="/profPerfil", status_code=303)


@app.get("/alunoAtualizar", response_class=HTMLResponse)
async def aluno_atualizar(request: Request, id: int, db=Depends(get_db), auth=Depends(verify_admin)):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, cpf, telefone, email FROM Aluno WHERE id = %s", (id,))
            aluno = cursor.fetchone()
    finally:
        db.close()
    return templates.TemplateResponse("alunos/alunoAtualizar.html", {
        "request": request,
        "aluno": aluno,
        "nome_usuario": request.session.get("nome_usuario")
    })


@app.post("/alunoAtualizar")
async def aluno_atualizar_post(
    request: Request,
    id: int = Form(...),
    nome: str = Form(...),
    telefone: str = Form(...),
    email: str = Form(...),
    db=Depends(get_db),
    auth=Depends(verify_admin)
):
    try:

        #regex
        if not validate_name(nome):
            request.session["mensagem"] = "Nome inválido"
            return RedirectResponse(url="/alunoAtualizar", status_code=303)
        
        if not validate_email(email):
            request.session["mensagem"] = "Email inválido"
            return RedirectResponse(url="/alunoAtualizar", status_code=303)
        
        if not validate_phone(telefone):
            request.session["mensagem"] = "Telefone inválido"
            return RedirectResponse(url="/alunoAtualizar", status_code=303)

        with db.cursor() as cursor:
            #att cpf e senha nao é aqui
            cursor.execute(
                "UPDATE Aluno SET nome=%s, telefone=%s, email=%s WHERE id=%s",
                (nome, telefone, email, id)
            )
            db.commit()
        request.session["mensagem"] = "Cadastro do aluno atualizado com sucesso!"
    except Exception as e:
        request.session["mensagem"] = f"Erro ao atualizar: {str(e)}"
    finally:
        db.close()
    return RedirectResponse(url="/profPerfil", status_code=303)

@app.get("/alunoSenha", response_class=HTMLResponse)
async def aluno_senha(request: Request, id: int, db=Depends(get_db), auth=Depends(verify_admin)):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome FROM Aluno WHERE id = %s", (id,))
            aluno = cursor.fetchone()
    finally:
        db.close()
    return templates.TemplateResponse("alunos/alunoSenha.html", {
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
    try:
        if not validate_password(nova_senha):
            request.session["mensagem"] = "Senha inválida"
            return RedirectResponse(url=f"/alunoSenha?id={id}", status_code=303)

        with db.cursor() as cursor:
            senha_hash = hash_password(nova_senha)
            cursor.execute("UPDATE Aluno SET senha=%s WHERE id=%s", (senha_hash, id))
            db.commit()
        request.session["mensagem"] = "Senha do aluno atualizada com sucesso!"
    except Exception as e:
        request.session["mensagem"] = f"Erro ao atualizar senha: {str(e)}"
    finally:
        db.close()
    return RedirectResponse(url="/profPerfil", status_code=303)

@app.post("/alunoExcluirConta")
async def aluno_excluir_conta(
    request: Request,
    db=Depends(get_db),
    auth=Depends(verify_logged_in)
):
    usuario_id = request.session.get("usuario_id")
    try:
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM Aluno WHERE id = %s", (usuario_id,))
            db.commit()
        request.session.clear()
    except Exception as e:
        request.session["mensagem"] = f"Erro ao excluir conta: {str(e)}"
        return RedirectResponse(url="/alunoPerfil", status_code=303)
    finally:
        db.close()
    return RedirectResponse(url="/", status_code=303)


@app.post("/alunoAtualizarFoto")
async def aluno_atualizar_foto(
    request: Request,
    fotoPerfil: UploadFile = File(None),
    db=Depends(get_db),
    auth=Depends(verify_logged_in)
):
    try:
        usuario_id = request.session.get("usuario_id")
        
        foto_bytes = None
        if fotoPerfil and fotoPerfil.filename:
            foto_bytes = await fotoPerfil.read()
            
            with db.cursor() as cursor:
                cursor.execute(
                    "UPDATE Aluno SET fotoPerfil=%s WHERE id=%s",
                    (foto_bytes, usuario_id)
                )
                db.commit()
                
        request.session["mensagem"] = "Foto de perfil atualizada com sucesso!"
    except Exception as e:
        request.session["mensagem"] = f"Erro ao atualizar foto: {str(e)}"
    finally:
        db.close()
        
    return RedirectResponse(url="/alunoPerfil", status_code=303)











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
    
    return templates.TemplateResponse("aulas/aulaListar.html", {
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
    return templates.TemplateResponse("aulas/aulaIncluir.html", {
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
    return RedirectResponse(url="/profPerfil", status_code=303)


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
    return templates.TemplateResponse("aulas/aulaExcluir.html", {
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
    return RedirectResponse(url="/profPerfil", status_code=303)


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
    return templates.TemplateResponse("aulas/aulaAtualizar.html", {
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
    return RedirectResponse(url="/profPerfil", status_code=303)



