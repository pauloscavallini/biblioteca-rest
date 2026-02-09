from flask import Flask, jsonify, request
from main import app, con

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
        data = request.get_json()

        titulo = data.get('titulo')
        autor = data.get('autor')
        ano_publicacao = data.get('ano_publicacao')

        cur = con.cursor()
        cur.execute("SELECT 1 FROM LIVRO WHERE TITULO = ?", (titulo,))
        if cur.fetchone():
            return jsonify({"error": "Livro ja cadastrado"}), 400

        cur.execute("""INSERT INTO LIVRO (titulo, autor, ano_publicacao)
        VALUES (?, ?, ?)""", (titulo, autor, ano_publicacao))

        con.commit()

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

        data = request.get_json()
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
        })
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