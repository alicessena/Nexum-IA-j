from database.user_manager import GerenciadorUsuarios 
from database import fetch_all, fetch_one, execute_query

user_manager = GerenciadorUsuarios()

def service_get_all_workers():
    # Esta função parece interagir com uma tabela 'users' que pode não existir.
    # O ideal é usar o user_manager para listar os usuários.
    query = "SELECT id, nome, email, funcao FROM supply_chain.usuarios" 
    return fetch_all(query)

def service_get_worker(user_id):
    query = "SELECT id, nome, email, funcao FROM supply_chain.usuarios WHERE id = ?"
    return fetch_one(query, (user_id,))

def service_create_worker(data):
    # CORREÇÃO: Passando todos os argumentos necessários para criar_usuario
    return user_manager.criar_usuario(
        nome=data.get('nome'),
        sobrenome=data.get('sobrenome'),
        data_nascimento=data.get('data_nascimento'),
        cpf=data.get('cpf'),
        funcao=data.get('funcao'),
        email=data.get('email'),
        senha=data.get('senha')
    )

def service_authenticate_user(usuario, senha):
    # CORREÇÃO: O método autenticar agora retorna uma tupla (sucesso, mensagem, nivel_acesso)
    authenticated, msg, nivel = user_manager.autenticar(usuario, senha)
    return authenticated, msg, nivel

def service_remove_worker(user_id):
    query = "DELETE FROM supply_chain.usuarios WHERE id = ?"
    success, deleted_count = execute_query(query, (user_id,))
    return success and deleted_count > 0