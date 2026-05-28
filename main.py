from __future__ import annotations
import pymysql
import base64
import hashlib
import hmac
import secrets
from typing import Optional 
from mangum import Mangum

from validators import validate_email, validate_cpf, validate_phone, validate_password, validate_drt, validate_name, validate_aula_nome, validate_birthday
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import UploadFile, File
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime

SESSION_IDLE_SECONDS = 3600
SESSION_COOKIE_MAX_AGE = 86400

app = FastAPI()

# Configuração de sessão
app.add_middleware(
    SessionMiddleware,
    secret_key="grip_secret",
    session_cookie="grip_session",
    max_age=SESSION_COOKIE_MAX_AGE,
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

REGEX_PATTERNS = {
    "regex_nome": r"[A-Za-zÀ-ÖØ-öø-ÿ\s']+",
    "regex_cpf": r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}",
    "regex_telefone": r"\(?\d{2}\)?\s?9\d{4}-?\d{4}",
    "regex_email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "regex_data_nascimento": r"\d{4}-\d{2}-\d{2}",
    "regex_senha": r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$",
}


def get_db():
    return pymysql.connect(**DB_CONFIG)


def _auth_redirect(url: str) -> None:
    raise HTTPException(status_code=303, headers={"Location": url})


def _enforce_session_activity(request: Request) -> None:
    if not request.session.get("user_logged_in"):
        _auth_redirect("/login")

    now = datetime.now()
    last_raw = request.session.get("last_activity")
    if last_raw:
        try:
            last_activity = datetime.fromisoformat(last_raw)
            if (now - last_activity).total_seconds() > SESSION_IDLE_SECONDS:
                request.session.clear()
                request.session["mensagem"] = "Sessão expirada por inatividade"
                _auth_redirect("/login")
        except ValueError:
            pass

    request.session["last_activity"] = now.isoformat()


def verify_logged_in(request: Request):
    _enforce_session_activity(request)


def verify_admin(request: Request):
    _enforce_session_activity(request)
    if request.session.get("perfil") != "admin":
        _auth_redirect("/")

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
    professores_publicos = []
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT id, nome, registro_drt, especialidade, fotoPerfil
                FROM Professor
                ORDER BY nome
                LIMIT 5
            """)
            professores_publicos = cursor.fetchall()
    finally:
        foto_b64 = get_user_foto_b64(request, db)
        db.close()

    for professor in professores_publicos:
        nome = (professor.get("nome") or "").strip()
        professor["iniciais"] = nome[0].upper() if nome else "P"
        professor["especialidade"] = professor.get("especialidade") or "Instrutor(a) Grip"
        foto = professor.get("fotoPerfil")
        professor["foto_b64"] = base64.b64encode(foto).decode("utf-8") if foto else None

    return templates.TemplateResponse("index.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario"),
        "foto_b64": foto_b64,
        "professores_publicos": professores_publicos
    })

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    if request.session.get("user_logged_in"):
        if request.session.get("perfil") == "admin":
            return RedirectResponse(url="/profPerfil", status_code=303)
        return RedirectResponse(url="/alunoPerfil", status_code=303)

    mensagem = request.session.pop("mensagem", None)
    form_data = request.session.pop("login_form", None)
    login_error = request.session.pop("login_error", None)
    if not mensagem and login_error:
        mensagem = login_error if login_error.startswith("Erro:") else f"Erro: {login_error}"

    return templates.TemplateResponse("cadastrologin/login.html", {
        "request": request,
        "mensagem": mensagem,
        "form_data": form_data,
        "status": "erro" if mensagem and mensagem.startswith("Erro:") else ("sucesso" 
  if mensagem else None)     
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
    professores_publicos = []
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT id, nome, registro_drt, especialidade, fotoPerfil
                FROM Professor
                ORDER BY nome
            """)
            professores_publicos = cursor.fetchall()
    finally:
        foto_b64 = get_user_foto_b64(request, db)
        db.close()

    for professor in professores_publicos:
        nome = (professor.get("nome") or "").strip()
        professor["iniciais"] = nome[0].upper() if nome else "P"
        professor["especialidade"] = professor.get("especialidade") or "Instrutor(a) Grip"
        foto = professor.get("fotoPerfil")
        professor["foto_b64"] = base64.b64encode(foto).decode("utf-8") if foto else None

    return templates.TemplateResponse("professores/professores.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario"),
        "foto_b64": foto_b64,
        "professores_publicos": professores_publicos
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
                request.session.pop("login_form", None)
                request.session["user_logged_in"] = True
                request.session["usuario_id"] = professor["id"]
                request.session["nome_usuario"] = professor["nome"]
                request.session["perfil"] = "admin" # <-- Define Professor como Admin
                request.session["last_activity"] = datetime.now().isoformat()
                return RedirectResponse(url="/profPerfil", status_code=303)

            #Aluno = User
            cursor.execute("SELECT id, nome, senha FROM Aluno WHERE email = %s", (Email,))
            aluno = cursor.fetchone()

            if aluno and verify_password(senha, aluno["senha"]):
                request.session.pop("login_form", None)
                request.session["user_logged_in"] = True
                request.session["usuario_id"] = aluno["id"]
                request.session["nome_usuario"] = aluno["nome"]
                request.session["email_usuario"] = Email
                request.session["perfil"] = "user" # <-- Define Aluno como User
                request.session["last_activity"] = datetime.now().isoformat()
                return RedirectResponse(url="/alunoPerfil", status_code=303)

            if not professor and not aluno:
                request.session["login_form"] = {"email": Email}
                request.session["mensagem"] = "Erro: Conta não encontrada."
            else:
                request.session["login_form"] = {"email": Email}
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
    aulas_legado = []
    aulas_agendadas = []
    plano_status = "sem_plano"
    mensagem = request.session.pop("mensagem", None)
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
            aulas_legado = cursor.fetchall()
            cursor.execute("""
                SELECT AG.id,
                       CONCAT('Aula ', UPPER(LEFT(AG.tipo_aula, 1)), SUBSTRING(AG.tipo_aula, 2)) AS nome,
                       AG.data_hora AS data,
                       AG.observacao AS descricao,
                       P.nome AS professor_nome
                FROM Agendamento_Aula AG
                INNER JOIN Professor P ON P.id = AG.fk_Professor_id
                WHERE AG.fk_Aluno_id = %s
                  AND AG.status = 'agendada'
                  AND AG.data_hora >= NOW()
                ORDER BY AG.data_hora ASC, AG.id ASC
                LIMIT 6
            """, (usuario_id,))
            aulas_agendadas = cursor.fetchall()
    finally:
        db.close()

    foto_b64 = None
    if aluno and aluno.get("fotoPerfil"):
        foto_b64 = base64.b64encode(aluno["fotoPerfil"]).decode("utf-8")

    from datetime import date as _date
    def _sort_key(aula):
        d = aula.get("data")
        if isinstance(d, _date) and not isinstance(d, datetime):
            d = datetime(d.year, d.month, d.day)
        return (d or datetime.min, aula.get("id", 0))

    aulas = sorted((aulas_legado or []) + (aulas_agendadas or []), key=_sort_key)[:6]

    for aula in aulas:
        if aula["data"]:
            d = aula["data"]
            if isinstance(d, datetime):
                aula["data_fmt"] = d.strftime("%d/%m/%Y %H:%M")
            else:
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
        "mensagem": mensagem,
    })


@app.post("/alunoPerfilAtualizar")
async def aluno_perfil_atualizar_post(
    request: Request,
    id: int = Form(...),
    nome: str = Form(...),
    email: str = Form(...),
    telefone: str = Form(""),
    db=Depends(get_db),
    auth=Depends(verify_logged_in)
):
    usuario_id = request.session.get("usuario_id")
    if id != usuario_id:
        raise HTTPException(status_code=403)
    try:
        if not validate_name(nome):
            request.session["mensagem"] = "Nome inválido"
            return RedirectResponse(url="/alunoPerfil", status_code=303)
        if not validate_email(email):
            request.session["mensagem"] = "Email inválido"
            return RedirectResponse(url="/alunoPerfil", status_code=303)
        if not validate_phone(telefone):
            request.session["mensagem"] = "Telefone inválido"
            return RedirectResponse(url="/alunoPerfil", status_code=303)
        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE Aluno SET nome=%s, email=%s, telefone=%s WHERE id=%s",
                (nome, email, telefone or None, id)
            )
            db.commit()
        request.session["nome_usuario"] = nome
        request.session["mensagem"] = "Perfil atualizado com sucesso!"
    except Exception as e:
        request.session["mensagem"] = f"Erro ao atualizar: {str(e)}"
    finally:
        db.close()
    return RedirectResponse(url="/alunoPerfil", status_code=303)


@app.get("/esqueci-senha", response_class=HTMLResponse)
async def esqueci_senha_get(request: Request):
    mensagem = request.session.pop("mensagem", None)
    return templates.TemplateResponse("cadastrologin/esqueciSenha.html", {
        "request": request,
        "mensagem": mensagem,
        "nome_usuario": request.session.get("nome_usuario"),
    })


@app.post("/esqueci-senha")
async def esqueci_senha_post(
    request: Request,
    email: str = Form(...),
    tipo: str = Form(...),
    db=Depends(get_db)
):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            tabela = "Professor" if tipo == "professor" else "Aluno"
            cursor.execute(f"SELECT id FROM {tabela} WHERE email = %s", (email,))
            user = cursor.fetchone()
    finally:
        db.close()
    if not user:
        request.session["mensagem"] = "E-mail não encontrado."
        return RedirectResponse(url="/esqueci-senha", status_code=303)
    request.session["reset_user_id"] = user["id"]
    request.session["reset_tipo"] = tipo
    return RedirectResponse(url="/redefinir-senha", status_code=303)


@app.get("/redefinir-senha", response_class=HTMLResponse)
async def redefinir_senha_get(request: Request):
    if not request.session.get("reset_user_id"):
        return RedirectResponse(url="/esqueci-senha", status_code=303)
    mensagem = request.session.pop("mensagem", None)
    return templates.TemplateResponse("cadastrologin/redefinirSenha.html", {
        "request": request,
        "mensagem": mensagem,
        "nome_usuario": request.session.get("nome_usuario"),
    })


@app.post("/redefinir-senha")
async def redefinir_senha_post(
    request: Request,
    nova_senha: str = Form(...),
    confirmar_senha: str = Form(...),
    db=Depends(get_db)
):
    user_id = request.session.get("reset_user_id")
    tipo = request.session.get("reset_tipo")
    if not user_id or not tipo:
        return RedirectResponse(url="/esqueci-senha", status_code=303)
    if nova_senha != confirmar_senha:
        request.session["mensagem"] = "As senhas não coincidem."
        return RedirectResponse(url="/redefinir-senha", status_code=303)
    if not validate_password(nova_senha):
        request.session["mensagem"] = "A senha deve ter pelo menos 8 caracteres, uma letra e um número."
        return RedirectResponse(url="/redefinir-senha", status_code=303)
    try:
        with db.cursor() as cursor:
            tabela = "Professor" if tipo == "professor" else "Aluno"
            cursor.execute(f"UPDATE {tabela} SET senha=%s WHERE id=%s", (hash_password(nova_senha), user_id))
            db.commit()
        request.session.pop("reset_user_id", None)
        request.session.pop("reset_tipo", None)
        request.session["mensagem"] = "Senha redefinida com sucesso!"
    except Exception as e:
        request.session["mensagem"] = f"Erro: {str(e)}"
        return RedirectResponse(url="/redefinir-senha", status_code=303)
    finally:
        db.close()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/professor-perfil", response_class=HTMLResponse)
async def professor_perfil_publico(
    request: Request,
    id: Optional[int] = None,
    db=Depends(get_db),
    auth=Depends(verify_logged_in)
):
    professor = None
    total_aulas_agendadas = 0
    total_alunos_unicos = 0
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            if id:
                cursor.execute("""
                    SELECT id, nome, registro_drt, cpf, email, especialidade, fotoPerfil
                    FROM Professor
                    WHERE id = %s
                """, (id,))
                professor = cursor.fetchone()
            else:
                cursor.execute("""
                    SELECT id, nome, registro_drt, cpf, email, especialidade, fotoPerfil
                    FROM Professor
                    ORDER BY nome
                    LIMIT 1
                """)
                professor = cursor.fetchone()

            if not professor:
                request.session["mensagem"] = "Erro: Professor não encontrado."
                return RedirectResponse(url="/professores", status_code=303)

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM Agendamento_Aula
                WHERE fk_Professor_id = %s
                  AND status = 'agendada'
                  AND data_hora >= NOW()
            """, (professor["id"],))
            total_aulas_agendadas = cursor.fetchone()["total"]

            cursor.execute("""
                SELECT COUNT(DISTINCT fk_Aluno_id) AS total
                FROM Agendamento_Aula
                WHERE fk_Professor_id = %s
            """, (professor["id"],))
            total_alunos_unicos = cursor.fetchone()["total"]
    finally:
        foto_b64 = get_user_foto_b64(request, db)
        db.close()

    professor_foto_b64 = None
    if professor and professor.get("fotoPerfil"):
        professor_foto_b64 = base64.b64encode(professor["fotoPerfil"]).decode("utf-8")

    mensagem = request.session.pop("mensagem", None)
    perfil = request.session.get("perfil")
    pode_agendar = perfil == "user"

    return templates.TemplateResponse("professores/professor-perfil.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario"),
        "foto_b64": foto_b64,
        "mensagem": mensagem,
        "status": "erro" if mensagem and mensagem.startswith("Erro") else None,
        "professor": professor,
        "professor_foto_b64": professor_foto_b64,
        "total_aulas_agendadas": total_aulas_agendadas,
        "total_alunos_unicos": total_alunos_unicos,
        "pode_agendar": pode_agendar,
        "hoje_data": datetime.now().strftime("%Y-%m-%d")
    })


@app.post("/agendar-aula")
async def agendar_aula(
    request: Request,
    professor_id: int = Form(...),
    tipo_aula: str = Form(...),
    data_aula: str = Form(...),
    hora_aula: str = Form(...),
    observacao: str = Form(""),
    db=Depends(get_db),
    auth=Depends(verify_logged_in)
):
    redirect_url = f"/professor-perfil?id={professor_id}"
    try:
        if request.session.get("perfil") != "user":
            request.session["mensagem"] = "Erro: Somente alunos podem realizar agendamentos."
            return RedirectResponse(url=redirect_url, status_code=303)

        tipos_validos = {"grupo", "particular"}
        if tipo_aula not in tipos_validos:
            request.session["mensagem"] = "Erro: Tipo de aula inválido."
            return RedirectResponse(url=redirect_url, status_code=303)

        try:
            data_hora = datetime.strptime(f"{data_aula} {hora_aula}", "%Y-%m-%d %H:%M")
        except ValueError:
            request.session["mensagem"] = "Erro: Data ou horário inválido."
            return RedirectResponse(url=redirect_url, status_code=303)

        if data_hora <= datetime.now():
            request.session["mensagem"] = "Erro: Escolha um horário futuro para o agendamento."
            return RedirectResponse(url=redirect_url, status_code=303)

        aluno_id = request.session.get("usuario_id")

        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id FROM Professor WHERE id = %s", (professor_id,))
            professor = cursor.fetchone()
            if not professor:
                request.session["mensagem"] = "Erro: Professor não encontrado."
                return RedirectResponse(url="/professores", status_code=303)

            cursor.execute("""
                SELECT id
                FROM Agendamento_Aula
                WHERE fk_Professor_id = %s
                AND data_hora = %s
                AND status = 'agendada'
                LIMIT 1
            """, (professor_id, data_hora))
            if cursor.fetchone():
                request.session["mensagem"] = "Erro: Esse horário já foi reservado para este professor."
                return RedirectResponse(url=f"/professor-perfil?id={professor_id}", status_code=303)

            cursor.execute("""
                SELECT id
                FROM Agendamento_Aula
                WHERE fk_Aluno_id = %s
                AND data_hora = %s
                AND status = 'agendada'
                LIMIT 1
            """, (aluno_id, data_hora))
            if cursor.fetchone():
                request.session["mensagem"] = "Erro: Você já possui um agendamento neste horário."
                return RedirectResponse(url=f"/professor-perfil?id={professor_id}", status_code=303)

            cursor.execute("""
                INSERT INTO Agendamento_Aula (fk_Aluno_id, fk_Professor_id, tipo_aula, data_hora, observacao, status)
                VALUES (%s, %s, %s, %s, %s, 'agendada')
            """, (aluno_id, professor_id, tipo_aula, data_hora, observacao))

            cursor.execute("""
                SELECT 1
                FROM Professor_Aluno
                WHERE fk_Professor_id = %s AND fk_Aluno_id = %s
                LIMIT 1
            """, (professor_id, aluno_id))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO Professor_Aluno (fk_Professor_id, fk_Aluno_id) VALUES (%s, %s)",
                    (professor_id, aluno_id)
                )

            db.commit()
            request.session["mensagem"] = "Aula agendada com sucesso!"
    except pymysql.MySQLError as e:
        db.rollback()
        request.session["mensagem"] = f"Erro: não foi possível concluir o agendamento ({str(e)})."
    finally:
        db.close()

    return RedirectResponse(url=redirect_url, status_code=303)


@app.get("/profPerfil", response_class=HTMLResponse)
async def prof_perfil(request: Request, db=Depends(get_db), auth=Depends(verify_admin)):
    usuario_id = request.session.get("usuario_id")
    agendamentos_futuros = []
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, registro_drt, cpf, email, especialidade, fotoPerfil FROM Professor WHERE id = %s", (usuario_id,))
            professor = cursor.fetchone()
            cursor.execute("SELECT id, nome, cpf, telefone, email, data_nascimento FROM Aluno ORDER BY nome")
            alunos = cursor.fetchall()
            cursor.execute("SELECT id, nome, registro_drt, cpf, email, especialidade FROM Professor ORDER BY nome")
            professores = cursor.fetchall()
            cursor.execute("""
                SELECT A.id, A.nome, A.data, A.descricao, P.nome AS professor_nome
                FROM Aula A
                LEFT JOIN Professor P ON A.fk_Professor_id = P.id
                ORDER BY A.data DESC
            """)
            aulas = cursor.fetchall()
            cursor.execute("""
                SELECT AG.id, AG.tipo_aula, AG.data_hora, AG.observacao, AL.nome AS aluno_nome
                FROM Agendamento_Aula AG
                INNER JOIN Aluno AL ON AL.id = AG.fk_Aluno_id
                WHERE AG.fk_Professor_id = %s
                AND AG.status = 'agendada'
                AND AG.data_hora >= NOW()
                ORDER BY AG.data_hora ASC, AG.id ASC
                LIMIT 6
            """, (usuario_id,))
            agendamentos_futuros = cursor.fetchall()
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

    for agendamento in agendamentos_futuros:
        data_hora = agendamento.get("data_hora")
        if data_hora:
            if isinstance(data_hora, datetime):
                agendamento["data_fmt"] = data_hora.strftime("%d/%m/%Y %H:%M")
            else:
                agendamento["data_fmt"] = data_hora.strftime("%d/%m/%Y") if hasattr(data_hora, "strftime") else str(data_hora)
        else:
            agendamento["data_fmt"] = "Data não informada"
        tipo_aula = (agendamento.get("tipo_aula") or "").strip().lower()
        agendamento["tipo_fmt"] = tipo_aula.capitalize() if tipo_aula else "Aula"

    mensagem = request.session.pop("mensagem", None)
    mensagem_tab = None
    if mensagem:
        mensagem_lower = mensagem.lower()
        if "aula" in mensagem_lower:
            mensagem_tab = "aulas"
        elif "aluno" in mensagem_lower:
            mensagem_tab = "alunos"
        elif "professor" in mensagem_lower:
            mensagem_tab = "professores"
        elif "senha" in mensagem_lower or "foto" in mensagem_lower:
            mensagem_tab = "configuracoes"
        else:
            mensagem_tab = "visao-geral"

    return templates.TemplateResponse("professores/profPerfil.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario"),
        "perfil": request.session.get("perfil"),
        "professor": professor,
        "foto_b64": foto_b64,
        "alunos": alunos,
        "professores": professores,
        "aulas": aulas,
        "total_alunos": len(alunos),
        "total_professores": len(professores),
        "total_aulas": len(aulas),
        "agendamentos_futuros": agendamentos_futuros,
        "mensagem": mensagem,
        "mensagem_tab": mensagem_tab,
    })


@app.get("/cadastro", response_class=HTMLResponse)
async def cadastro_page(request: Request):
    mensagem = request.session.pop("mensagem", None)
    form_data = request.session.pop("cadastro_form", None)
    return templates.TemplateResponse("cadastrologin/cadastro.html", {
        "request": request,
        "mensagem": mensagem,
        "form_data": form_data,
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
    termos: Optional[str] = Form(None),
    db=Depends(get_db)
):
    def stash_form():
        request.session["cadastro_form"] = {
            "nome": nome,
            "email": email,
            "telefone": telefone,
            "cpf": cpf,
            "data_nascimento": data_nascimento,
            "termos": bool(termos),
        }

    try:
        if not data_nascimento:
            stash_form()
            request.session["mensagem"] = "Erro: Informe sua data de nascimento."
            return RedirectResponse(url="/cadastro", status_code=303)

        if not senha:
            stash_form()
            request.session["mensagem"] = "Erro: Informe uma senha."
            return RedirectResponse(url="/cadastro", status_code=303)

        if len(nome.strip().split()) < 2:
            stash_form()
            request.session["mensagem"] = "Erro: Informe nome e sobrenome."
            return RedirectResponse(url="/cadastro", status_code=303)

        if not validate_name(nome):
            stash_form()
            request.session["mensagem"] = "Erro: Nome inválido."
            return RedirectResponse(url="/cadastro", status_code=303)

        if not validate_email(email):
            stash_form()
            request.session["mensagem"] = "Erro: E-mail inválido."
            return RedirectResponse(url="/cadastro", status_code=303)

        if not validate_cpf(cpf):
            stash_form()
            request.session["mensagem"] = "Erro: CPF inválido."
            return RedirectResponse(url="/cadastro", status_code=303)

        if not validate_phone(telefone):
            stash_form()
            request.session["mensagem"] = "Erro: Telefone inválido."
            return RedirectResponse(url="/cadastro", status_code=303)

        if not validate_birthday(data_nascimento):
            stash_form()
            request.session["mensagem"] = "Erro: Data de nascimento inválida."
            return RedirectResponse(url="/cadastro", status_code=303)

        if not termos:
            stash_form()
            request.session["mensagem"] = "Erro: Você precisa aceitar os termos para continuar."
            return RedirectResponse(url="/cadastro", status_code=303)

        if not validate_password(senha):
            stash_form()
            request.session["mensagem"] = "Erro: A senha não atende aos requisitos."
            return RedirectResponse(url="/cadastro", status_code=303)

        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM Aluno WHERE email = %s", (email,))
            if cursor.fetchone():
                stash_form()
                request.session["mensagem"] = "Erro: Este e-mail já está em uso!"
                return RedirectResponse(url="/cadastro", status_code=303)

            cursor.execute("SELECT id FROM Aluno WHERE cpf = %s", (cpf,))
            if cursor.fetchone():
                stash_form()
                request.session["mensagem"] = "Erro: Este CPF já está em uso!"
                return RedirectResponse(url="/cadastro", status_code=303)

            senha_hash = hash_password(senha)
            cursor.execute(
                "INSERT INTO Aluno (nome, cpf, telefone, email, senha, data_nascimento) VALUES (%s, %s, %s, %s, %s, %s)",
                (nome, cpf, telefone, email, senha_hash, data_nascimento)
            )
            aluno_id = cursor.lastrowid
            db.commit()
            request.session["user_logged_in"] = True
            request.session["usuario_id"] = aluno_id
            request.session["nome_usuario"] = nome
            request.session["email_usuario"] = email
            request.session["perfil"] = "user"
            request.session["last_activity"] = datetime.now().isoformat()
            request.session["mensagem"] = "Aluno cadastrado com sucesso!"
            return RedirectResponse(url="/alunoPerfil", status_code=303)

    except pymysql.err.IntegrityError:
        stash_form()
        request.session["mensagem"] = "Erro: E-mail ou CPF já cadastrado."
        return RedirectResponse(url="/cadastro", status_code=303)
    except Exception as e:
        stash_form()
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
            cursor.execute("SELECT id, nome, registro_drt, cpf, email, especialidade FROM Professor ORDER BY nome")
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
    mensagem = request.session.pop("mensagem", None)
    return templates.TemplateResponse("professores/profIncluir.html", {
        "request": request,
        "nome_usuario": request.session.get("nome_usuario"),
        "mensagem": mensagem
    })


@app.post("/profIncluir")
async def prof_incluir_post(
    request: Request,
    nome: str = Form(...),
    registro_drt: str = Form(...),
    cpf: str = Form(""),
    telefone: str = Form(""),
    email: str = Form(...),
    senha: str = Form(...),
    especialidade: str = Form(""),
    fotoPerfil: UploadFile = File(None),
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

        if not validate_phone(telefone):
            request.session["mensagem"] = "Telefone inválido"
            return RedirectResponse(url="/profIncluir", status_code=303)
        
        if not validate_drt(registro_drt):
            request.session["mensagem"] = "Registro DRT inválido"
            return RedirectResponse(url="/profIncluir", status_code=303)
        

        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM Professor WHERE email = %s", (email,))
            if cursor.fetchone():
                request.session["mensagem"] = "Erro: Este e-mail já está em uso!"
                return RedirectResponse(url="/profIncluir", status_code=303)

            senha_hash = hash_password(senha)
            foto_bytes = await fotoPerfil.read() if fotoPerfil and fotoPerfil.filename else None
            cursor.execute(
                "INSERT INTO Professor (nome, registro_drt, cpf, telefone, email, senha, especialidade, fotoPerfil) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (nome, registro_drt, cpf, telefone, email, senha_hash, especialidade or None, foto_bytes)
            )
            db.commit()
        request.session["mensagem"] = "Professor cadastrado com sucesso!"
    except pymysql.err.IntegrityError:
        request.session["mensagem"] = "Erro: E-mail já cadastrado."
    except Exception as e:
        request.session["mensagem"] = f"Erro ao cadastrar: {str(e)}"
    finally:
        db.close()
    return RedirectResponse(url="/profPerfil", status_code=303)


@app.get("/profExcluir", response_class=HTMLResponse)
async def prof_excluir(request: Request, id: int, db=Depends(get_db), auth=Depends(verify_admin)):
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, nome, registro_drt, cpf, telefone, email, fotoPerfil FROM Professor WHERE id = %s", (id,))
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
            cursor.execute("SELECT id, nome, registro_drt, cpf, telefone, email, especialidade, fotoPerfil FROM Professor WHERE id = %s", (id,))
            professor = cursor.fetchone()
    finally:
        db.close()
    foto_b64 = None
    if professor and professor.get("fotoPerfil"):
        import base64
        foto_b64 = base64.b64encode(professor["fotoPerfil"]).decode("utf-8")
    return templates.TemplateResponse("professores/profAtualizar.html", {
        "request": request,
        "prof": professor,
        "foto_b64": foto_b64,
        "nome_usuario": request.session.get("nome_usuario")
    })


@app.post("/profAtualizar")
async def prof_atualizar_post(
    request: Request,
    id: int = Form(...),
    nome: str = Form(...),
    email: str = Form(...),
    telefone: str = Form(""),
    especialidade: str = Form(""),
    fotoPerfil: UploadFile = File(None),
    db=Depends(get_db),
    auth=Depends(verify_admin)
):
    try:

        if not validate_name(nome):
            request.session["mensagem"] = "Nome inválido"
            return RedirectResponse(url=f"/profAtualizar?id={id}", status_code=303)

        if not validate_email(email):
            request.session["mensagem"] = "Email inválido"
            return RedirectResponse(url=f"/profAtualizar?id={id}", status_code=303)

        if not validate_phone(telefone):
            request.session["mensagem"] = "Telefone inválido"
            return RedirectResponse(url=f"/profAtualizar?id={id}", status_code=303)

        with db.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM Professor WHERE email = %s AND id != %s",
                (email, id)
            )
            if cursor.fetchone():
                request.session["mensagem"] = "Erro: Este e-mail já está em uso!"
                return RedirectResponse(url=f"/profAtualizar?id={id}", status_code=303)

            # Não atualizamos registro_drt, cpf e senha aqui
            foto_bytes = await fotoPerfil.read() if fotoPerfil and fotoPerfil.filename else None
            if foto_bytes:
                cursor.execute(
                    "UPDATE Professor SET nome=%s, email=%s, telefone=%s, especialidade=%s, fotoPerfil=%s WHERE id=%s",
                    (nome, email, telefone, especialidade or None, foto_bytes, id)
                )
            else:
                cursor.execute(
                    "UPDATE Professor SET nome=%s, email=%s, telefone=%s, especialidade=%s WHERE id=%s",
                    (nome, email, telefone, especialidade or None, id)
                )
            db.commit()
        if id == request.session.get("usuario_id"):
            request.session["nome_usuario"] = nome
        request.session["mensagem"] = "Cadastro do professor atualizado com sucesso!"
    except pymysql.err.IntegrityError:
        request.session["mensagem"] = "Erro: E-mail já cadastrado."
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
        "nome_usuario": request.session.get("nome_usuario"),
        **REGEX_PATTERNS
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
            cursor.execute("SELECT id FROM Aluno WHERE email = %s", (email,))
            if cursor.fetchone():
                request.session["mensagem"] = "Erro: Este e-mail já está em uso!"
                return RedirectResponse(url="/alunoIncluir", status_code=303)

            cursor.execute("SELECT id FROM Aluno WHERE cpf = %s", (cpf,))
            if cursor.fetchone():
                request.session["mensagem"] = "Erro: Este CPF já está em uso!"
                return RedirectResponse(url="/alunoIncluir", status_code=303)

            senha_hash = hash_password(senha)
            cursor.execute(
                "INSERT INTO Aluno (nome, cpf, telefone, email, senha, data_nascimento) VALUES (%s, %s, %s, %s, %s, %s)",
                (nome, cpf, telefone, email, senha_hash, data_nascimento)
            )
            db.commit()
        request.session["mensagem"] = "Aluno cadastrado com sucesso!"
    except pymysql.err.IntegrityError:
        request.session["mensagem"] = "Erro: E-mail ou CPF já cadastrado."
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
            cursor.execute("SELECT id, nome, cpf, telefone, email, data_nascimento FROM Aluno WHERE id = %s", (id,))
            aluno = cursor.fetchone()
    finally:
        db.close()
    return templates.TemplateResponse("alunos/alunoAtualizar.html", {
        "request": request,
        "aluno": aluno,
        "nome_usuario": request.session.get("nome_usuario"),
        **REGEX_PATTERNS
    })


@app.post("/alunoAtualizar")
async def aluno_atualizar_post(
    request: Request,
    id: int = Form(...),
    nome: str = Form(...),
    telefone: str = Form(...),
    email: str = Form(...),
    data_nascimento: str = Form(...),
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

        if not validate_birthday(data_nascimento):
            request.session["mensagem"] = "Data de Nascimento inválida"
            return RedirectResponse(url="/alunoAtualizar", status_code=303)

        with db.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM Aluno WHERE email = %s AND id != %s",
                (email, id)
            )
            if cursor.fetchone():
                request.session["mensagem"] = "Erro: Este e-mail já está em uso!"
                return RedirectResponse(url=f"/alunoAtualizar?id={id}", status_code=303)

            #att cpf e senha nao é aqui
            cursor.execute(
                "UPDATE Aluno SET nome=%s, telefone=%s, email=%s, data_nascimento=%s WHERE id=%s",
                (nome, telefone, email, data_nascimento, id)
            )
            db.commit()
        request.session["mensagem"] = "Cadastro do aluno atualizado com sucesso!"
    except pymysql.err.IntegrityError:
        request.session["mensagem"] = "Erro: E-mail já cadastrado."
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
    q = (request.query_params.get("q") or "").strip()
    professor_id_raw = (request.query_params.get("professor_id") or "").strip()
    data_inicio = (request.query_params.get("data_inicio") or "").strip()
    data_fim = (request.query_params.get("data_fim") or "").strip()

    professor_id = professor_id_raw if professor_id_raw.isdigit() else ""

    if data_inicio:
        try:
            datetime.strptime(data_inicio, "%Y-%m-%d")
        except ValueError:
            data_inicio = ""

    if data_fim:
        try:
            datetime.strptime(data_fim, "%Y-%m-%d")
        except ValueError:
            data_fim = ""

    filtros = {
        "q": q,
        "professor_id": professor_id,
        "data_inicio": data_inicio,
        "data_fim": data_fim
    }

    professores_filtro = []
    aulas = []
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            where_clauses = []
            query_params = []

            if q:
                termo = f"%{q}%"
                where_clauses.append("(A.nome LIKE %s OR A.descricao LIKE %s OR P.nome LIKE %s)")
                query_params.extend([termo, termo, termo])

            if professor_id:
                where_clauses.append("A.fk_Professor_id = %s")
                query_params.append(int(professor_id))

            if data_inicio:
                where_clauses.append("DATE(A.data) >= %s")
                query_params.append(data_inicio)

            if data_fim:
                where_clauses.append("DATE(A.data) <= %s")
                query_params.append(data_fim)

            query = """
                SELECT A.id, A.nome, A.data, A.descricao, P.nome AS professor_nome
                FROM Aula A
                LEFT JOIN Professor P ON A.fk_Professor_id = P.id
            """
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            query += " ORDER BY A.data DESC"
            cursor.execute(query, query_params)
            aulas = cursor.fetchall()

            cursor.execute("SELECT id, nome FROM Professor ORDER BY nome")
            professores_filtro = cursor.fetchall()
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
        "professores_filtro": professores_filtro,
        "filtros": filtros,
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
        if not validate_aula_nome(nome):
            request.session["mensagem"] = "Nome da aula inválido"
            return RedirectResponse(url="/aulaIncluir", status_code=303)

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
        if not validate_aula_nome(nome):
            request.session["mensagem"] = "Nome da aula inválido"
            return RedirectResponse(url="/aulaAtualizar", status_code=303)

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
