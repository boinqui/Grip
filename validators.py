import re
from validate_docbr import CPF
from pregex.core.classes import Digit, Letter, AnyButWhitespace
from pregex.core.quantifiers import AtLeast, Exactly, Optional
from pregex.core.operators import Sequence, Either
from pregex.core.assertions import MatchAtStart, MatchAtEnd
from pregex.core.classes import AnyFrom

cpf_validator = CPF()

def validate_email(email: str) -> bool:
    #texto + @ + texto + . + 2 ou mais letras
    email_pattern = Sequence(
        AtLeast(AnyButWhitespace(), 1),
        "@",
        AtLeast(AnyButWhitespace(), 1),
        ".",
        AtLeast(Letter(), 2)
    )
    # get_matches valida a string inteira se usarmos de forma estrita
    return email_pattern.matches(email)

def validate_cpf(cpf: str) -> bool:
    return cpf_validator.validate(cpf)

def validate_phone(phone: str) -> bool:
    # 1. Remove tudo o que não for número (parênteses, hifens, espaços)
    phone_digits = re.sub(r'\D', '', phone)
    
    # 2. Define o padrão ideal: DDD (2 dígitos) + 9 + Número (8 dígitos) = 11 dígitos
    phone_pattern = Sequence(
        Exactly(Digit(), 2),  # DDD
        "9",                  # 9 obrigatório para celular
        Exactly(Digit(), 8)   # Restante do número
    )
    
    # 3. Valida a string limpa
    return phone_pattern.matches(phone_digits)

def validate_password(password: str) -> bool:
    if len(password) < 8:
        return False
    
    # 2. Varre a string caractere por caractere fazendo a pergunta lógica
    tem_letra = any(caractere.isalpha() for caractere in password)
    tem_numero = any(caractere.isdigit() for caractere in password)
    
    # A senha só é válida se ambos os testes forem True
    return tem_letra and tem_numero

def validate_drt(drt: str) -> bool:
    drt_pattern = Sequence("DRT-", AtLeast(Digit(), 1))
    return drt_pattern.matches(drt)

def validate_name(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    letras_e_acentos = AnyFrom("A-Za-zÀ-ÖØ-öø-ÿ ")
    name_pattern = AtLeast(letras_e_acentos, 1)
    
    return name_pattern.matches(name)