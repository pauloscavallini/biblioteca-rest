import re
from flask_bcrypt import generate_password_hash, check_password_hash

def verificar_senha_forte(senha):
    if len(senha) < 8:
        return
    if not any(char.isupper() for char in senha):
        return
    if not any(char.islower() for char in senha):
        return
    if not any(char.isdigit() for char in senha):
        return
    if not any(char in "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~" for char in senha):
        return
    return True


def criptografar(senha):
    return generate_password_hash(senha).decode("utf-8")


def senha_correta(senha_cripto, senha):
    return check_password_hash(senha_cripto, senha)

def limpar_email(email):
    if not email:
        return email
    return re.sub(r'\s+', '', email).strip().lower()