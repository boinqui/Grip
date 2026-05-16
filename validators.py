from validate_docbr import CPF
import re
from pregex.core.classes import AnyDigit, AnyLetter, AnyButWhitespace, AnyBetween, AnyWhitespace
from pregex.core.quantifiers import AtLeast, Exactly
from pregex.core.operators import Either
from datetime import date

cpf_validator = CPF()

def validate_email(email: str) -> bool:
    pattern = (
        AtLeast(AnyButWhitespace(), 1) +
        '@' +
        AtLeast(AnyButWhitespace(), 1) +
        '.' +
        AtLeast(AnyLetter(), 2)
    )
    return pattern.is_exact_match(email)

def validate_cpf(cpf: str) -> bool:
    return cpf_validator.validate(cpf)

def validate_phone(phone: str) -> bool:
    phone_digits = re.sub(r'\D', '', phone)
    pattern = Exactly(AnyDigit(), 2) + '9' + Exactly(AnyDigit(), 8)
    return pattern.is_exact_match(phone_digits)

def validate_password(password: str) -> bool:
    if len(password) < 8:
        return False
    return any(c.isalpha() for c in password) and any(c.isdigit() for c in password)

def validate_drt(drt: str) -> bool:
    pattern = 'DRT-' + AtLeast(AnyDigit(), 1)
    return pattern.is_exact_match(drt)

def validate_name(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    letras = Either(
        AnyBetween('A', 'Z'), AnyBetween('a', 'z'),
        AnyBetween('À', 'Ö'), AnyBetween('Ø', 'ö'),
        AnyBetween('ø', 'ÿ'), AnyWhitespace()
    )
    return AtLeast(letras, 1).is_exact_match(name)

def validate_birthday(birthday: str) -> bool:
    try:

        birth_date = date.fromisoformat(birthday)
    except (ValueError, TypeError):
        return False
        
    today = date.today()

    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    MIN_AGE = 18
    MAX_AGE = 100
    
    return MIN_AGE <= age <= MAX_AGE