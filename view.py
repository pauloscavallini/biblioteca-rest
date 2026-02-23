import os
import threading

from flask import jsonify, request, send_file, Response
from fpdf import FPDF
from funcao import *
from main import app, con
import pygal

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/listar_livros', methods=['GET'])
def listar_livro():
    try:
        cur = con.cursor()
        cur.execute("SELECT id_livro, titulo, autor, ano_publicacao FROM livro")
        livros = cur.fetchall()
        listaLivros = []

        for livro in livros:
            listaLivros.append({
                'id_livro': livro[0],
                'titulo': livro[1],
                'autor': livro[2],
                'ano_publicacao': livro[3],
            })

        return jsonify(mensagem="Lista de livros", livros=listaLivros), 200
    except Exception as e:
        return jsonify({"message": f"Erro ao consultar banco de dados {e}"}), 500
    finally:
        cur.close()


@app.route('/criar_livro', methods=['POST'])
def criar_livro():
    try:
        titulo = request.form.get('titulo')
        autor = request.form.get('autor')
        ano_publicacao = request.form.get('ano_publicacao')
        imagem = request.files.get('imagem')

        cur = con.cursor()
        cur.execute("SELECT 1 FROM LIVRO WHERE TITULO = ?", (titulo,))
        if cur.fetchone():
            return jsonify({"error": "Livro ja cadastrado"}), 400

        cur.execute("""INSERT INTO LIVRO (titulo, autor, ano_publicacao)
        VALUES (?, ?, ?) RETURNING id_livro""", (titulo, autor, ano_publicacao))

        codigo_livro = cur.fetchone()[0]
        con.commit()

        caminho_imagem = None

        if imagem:
            nome_imagem = f"{codigo_livro}.jpg"
            caminho_imagem_destino = os.path.join(app.config['UPLOAD_FOLDER'], "Livros")
            os.makedirs(caminho_imagem_destino, exist_ok=True)
            caminho_imagem = os.path.join(caminho_imagem_destino, nome_imagem)
            imagem.save(caminho_imagem)

        return jsonify({
            "message": "Livro cadastrado com sucesso",
            "livro": {
                "titulo": titulo,
                "autor": autor,
                "ano_publicacao": ano_publicacao
            }}), 201
    except Exception as e:
        return jsonify({"error": f"Erro ao consultar banco de dados {e}"}), 500
    finally:
        cur.close()


@app.route('/editar_livro/<int:id>', methods=['PUT'])
def editar_livro(id):
    try:
        cur = con.cursor()
        cur.execute("SELECT id_livro, titulo, autor, ano_publicacao FROM livro WHERE id_livro = ?", (id,))

        tem_livro = cur.fetchone()

        if not tem_livro:
            return jsonify({"error": "Livro nao encontrado"}), 404

        data = request.get_json(silent=True)

        if not data:
            return jsonify({"error": "Formato de requisicao invalido"}), 400

        titulo = data.get('titulo')
        autor = data.get('autor')
        ano_publicacao = data.get('ano_publicacao')

        cur.execute("""UPDATE livro set titulo = ?, autor = ?, ano_publicacao = ?
        WHERE id_livro = ?
        """, (titulo, autor, ano_publicacao, id))

        con.commit()

        return jsonify({
            "message": "Livro atualizado com sucesso",
            "livro": {
                "id_livro": id,
                "titulo": titulo,
                "autor": autor,
                "ano_publicacao": ano_publicacao
            }
        }), 200
    except Exception as e:
        return jsonify({
            "error": "Houve um erro ao editar livro"
        }), 500
    finally:
        cur.close()


@app.route('/deletar_livro/<int:id>', methods=['DELETE'])
def deletar_livro(id):
    try:
        cur = con.cursor()

        cur.execute("select 1 from livro where id_livro = ?", (id,))
        if not cur.fetchone():
            return jsonify({"error": "Livro nao encontrado"}), 404

        cur.execute("delete from livro where id_livro = ?", (id,))
        con.commit()

        return jsonify({"message": "Livro deletado com sucesso", "id_livro": id})
    except Exception as e:
        return jsonify({"error": "Houve um erro ao excluir livro"})
    finally:
        cur.close()


@app.route('/criar_usuario', methods=['POST'])
def criar_usuario():
    try:
        cur = con.cursor()
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"error": "Formato de requisicao invalido"}), 400

        # limpando email pra nao ficar feio no db
        email = limpar_email(data.get('email'))
        nome = data.get('nome')
        senha = data.get('senha')

        if not email or not senha or not nome:
            return jsonify({"error": "Email, nome e senha são obrigatorios"}), 400

        if not verificar_senha_forte(senha):
            return jsonify({"error": "Senha fraca"}), 400

        cur.execute("select 1 from usuario where email = ?", (email,))

        if cur.fetchone():
            return jsonify({"error": "Email ja cadastrado"}), 400

        nome = nome.strip()
        senha = senha.strip()

        cur.execute("insert into usuario (email, nome, senha) values (?, ?, ?)",
                    (email, nome, criptografar(senha)))

        con.commit()

        return jsonify({
            "message": "Usuario cadastrado com sucesso",
            "usuario": {
                "email": email,
                "nome": nome,
            }
        }), 201
    except Exception as e:
        return jsonify({"error": f"Houve um erro ao criar usuario {e}"}), 500
    finally:
        cur.close()


@app.route('/editar_usuario/<int:id>', methods=['PUT'])
def editar_usuario(id):
    try:
        cur = con.cursor()
        cur.execute("select id_usuario, email, nome, senha from usuario where id_usuario = ?", (id,))

        if not cur.fetchone():
            return jsonify({"error": "Usuario nao encontrado"}), 404

        data = request.get_json(silent=True)

        if not data:
            return jsonify({"error": "Formato de requisicao invalido"}), 400

        email = limpar_email(data.get('email'))
        nome = data.get('nome')
        senha = data.get('senha')

        if not email or not senha or not nome:
            return jsonify({"error": "Email, nome e senha são obrigatorios"}), 400

        # estou buscando pelo id do usuário que tenha o mesmo email informado na requisicao
        cur.execute("SELECT id_usuario from usuario where email = ?", (email,))
        usuario = cur.fetchone()

        if usuario:
            id_email_encontrado = usuario[0]

            # se nao for encontrado email relacionado, passa aqui
            # ou mesmo que encontrar, mas for outro usuario
            if id_email_encontrado != id:
                return jsonify({"error": "Email ja utilizado"})

        cur.execute("UPDATE usuario SET email = ?, nome = ?, senha = ? WHERE id_usuario = ?",
                    (email, nome, criptografar(senha), id))

        con.commit()

        return jsonify({
            "message": "Usuario atualizado com sucesso",
            "usuario": {
                "email": email,
                "nome": nome,
            }
        }), 200
    except Exception as e:
        return jsonify({"error": f"Houve um erro ao editar usuario: {e}"}), 500
    finally:
        cur.close()


@app.route('/login', methods=['POST'])
def login():
    try:
        cur = con.cursor()
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"error": "Formato de requisicao invalido"}), 400

        email = limpar_email(data.get('email'))
        senha = data.get('senha')

        if not email or not senha:
            return jsonify({"error": "Email e senha são obrigatorios"}), 400

        cur.execute("SELECT senha from usuario WHERE email = ?", (email,))

        senha_criptografada = cur.fetchone()[0]

        if not senha_criptografada:
            return jsonify({"error": "Usuario nao encontrado"}), 404

        if not senha_correta(senha_criptografada, senha):
            return jsonify({"error": "Senha incorreta"}), 401

        return jsonify({"message": "Login realizado"}), 200
    except Exception as e:
        return jsonify({"error": f"Houve um erro ao fazer login {e}"}), 500
    finally:
        cur.close()

@app.route('/deletar_usuario/<int:id>', methods=['DELETE'])
def deletar_usuario(id):
    try:
        cur = con.cursor()

        if not id:
            return jsonify({"error": "Formato invalido, informe um id"}), 400

        cur.execute("select 1 from usuario where id_usuario = ?", (id,))

        if not cur.fetchone():
            return jsonify({"error": "Usuario nao encontrado"}), 404

        cur.execute("delete from usuario where id_usuario = ?", (id,))
        con.commit()

        return jsonify({"message": "Usuario excluido com sucesso"}), 200
    except Exception as e:
        return jsonify({"error": f"Houve um erro ao fazer login {e}"}), 500
    finally:
        cur.close()


@app.route('/relatorio_livros', methods=['GET'])
def relatorio_livros():
    try:
        cur = con.cursor()
        cur.execute("SELECT ID_LIVRO, TITULO, AUTOR, ANO_PUBLICACAO FROM LIVRO l ")
        livros = cur.fetchall()

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", style='B', size=16)
        pdf.cell(200, 10, "Relatorio de Livros", ln=True, align='C')

        pdf.ln(5)  # Espaço entre o título e a linha
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())  # Linha abaixo do título
        pdf.ln(5)  # Espaço após a linha

        pdf.set_font("Arial", size=12)
        for livro in livros:
            pdf.cell(200, 10, f"ID: {livro[0]} - {livro[1]} - {livro[2]} - {livro[3]}", ln=True)

        contador_livros = len(livros)
        pdf.ln(10)
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(200, 10, f"Total de livros cadastrados: {contador_livros}", ln=True, align='C')

        pdf_path = "relatorio_livros.pdf"
        pdf.output(pdf_path)
        return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')
    except Exception as e:
        return jsonify({"error": "Houve um erro ao gerar pdf"}), 500
    finally:
        cur.close()

@app.route('/grafico', methods=['GET'])
def grafico():
    try:
        cur = con.cursor()
        cur.execute("""select ano_publicacao, count(*)
                           from livro
                           group by ano_publicacao
                           order by ano_publicacao
            """)

        resultado = cur.fetchall()

        grafico = pygal.Bar()
        grafico.title = "Quantidade de livros por ano de publicação"

        for i in resultado:
            grafico.add(str(i[0]), i[1])
        return Response(grafico.render(), mimetype='image/svg+xml')
    except Exception as e:
        return jsonify({"error": "Erro ao consultar banco de dados"}), 500
    finally:
        cur.close()

@app.route('/enviar_email', methods=["POST"])
def enviar_email():
    try:
        dados = request.get_json()
        assunto = dados["subject"]
        mensagem = dados["message"]
        destinatario = dados["to"]

        thread = threading.Thread(target=envio_email, args=(destinatario, assunto, mensagem))

        thread.start()

        return jsonify({"message": "E-mail enviado com sucesso"}), 200
    except Exception as e:
        return jsonify({"message": "Houve um erro ao enviar e-mail"}), 500