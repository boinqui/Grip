import re


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
