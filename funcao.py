from flask_bcrypt import generate_password_hash, check_password_hash

def verificarSenhaForte(senha):
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
    return generate_password_hash(senha)