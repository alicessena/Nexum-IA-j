"""
Gerenciador de Usuários - Nexum Supply Chain
Autor: BBTS Nexum Team
Data: 2025-10-15
"""

import pyodbc
import bcrypt
import re
from datetime import datetime, date
from typing import Optional, Dict, List, Tuple
import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuração de Conexão ---
AZURE_SQL_CONFIG = {
    'server': os.getenv('AZURE_SQL_SERVER', 'seu-servidor.database.windows.net'),
    'database': os.getenv('AZURE_SQL_DATABASE', 'nexum-supply-chain'),
    'username': os.getenv('AZURE_SQL_USERNAME', 'seu-usuario'),
    'password': os.getenv('AZURE_SQL_PASSWORD', 'sua-senha'),
    'driver': '{ODBC Driver 18 for SQL Server}'
}

def get_connection():
    """Estabelece conexão com o banco de dados."""
    conn_str = (
        f"DRIVER={AZURE_SQL_CONFIG['driver']};"
        f"SERVER={AZURE_SQL_CONFIG['server']};"
        f"DATABASE={AZURE_SQL_CONFIG['database']};"
        f"UID={AZURE_SQL_CONFIG['username']};"
        f"PWD={AZURE_SQL_CONFIG['password']};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)

# --- Funções de Validação ---

def validar_cpf(cpf: str) -> bool:
    """Valida CPF (apenas números)."""
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    
    def calcular_digito(cpf_parcial):
        soma = sum(int(cpf_parcial[i]) * (len(cpf_parcial) + 1 - i) for i in range(len(cpf_parcial)))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    if int(cpf[9]) != calcular_digito(cpf[:9]) or int(cpf[10]) != calcular_digito(cpf[:10]):
        return False
    
    return True

def validar_email(email: str) -> bool:
    """Valida formato de email."""
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(padrao, email))

def validar_senha(senha: str) -> Tuple[bool, str]:
    """Valida força da senha."""
    if len(senha) < 8:
        return False, "A senha deve ter no mínimo 8 caracteres."
    if not re.search(r'[A-Z]', senha):
        return False, "A senha deve conter pelo menos uma letra maiúscula."
    if not re.search(r'[a-z]', senha):
        return False, "A senha deve conter pelo menos uma letra minúscula."
    if not re.search(r'[0-9]', senha):
        return False, "A senha deve conter pelo menos um número."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
        return False, "A senha deve conter pelo menos um caractere especial."
    return True, "Senha válida."

def limpar_cpf(cpf: str) -> str:
    """Remove formatação do CPF."""
    return re.sub(r'[^0-9]', '', cpf)

# --- Funções de Hash de Senha ---

def hash_senha(senha: str) -> str:
    """Gera hash bcrypt da senha."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    """Verifica se a senha corresponde ao hash."""
    return bcrypt.checkpw(senha.encode('utf-8'), hash_armazenado.encode('utf-8'))

# --- Classe GerenciadorUsuarios ---

class GerenciadorUsuarios:
    """Gerencia operações de usuários no banco de dados."""
    
    FUNCOES_VALIDAS = ['admin', 'analista', 'operador', 'gerente', 'visualizador']
    
    def __init__(self):
        self.conn = None

    def conectar(self):
        """Estabelece conexão com o banco."""
        if not self.conn:
            self.conn = get_connection()
    
    def desconectar(self):
        """Fecha conexão com o banco."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def criar_usuario(self, nome: str, sobrenome: str, data_nascimento: date, cpf: str, funcao: str, email: str, senha: str, criado_por: Optional[int] = None) -> Tuple[bool, str]:
        """Cria um novo usuário."""
        self.conectar()
        cursor = self.conn.cursor()
        try:
            cpf_limpo = limpar_cpf(cpf)
            if not validar_cpf(cpf_limpo):
                return False, "CPF inválido."
            
            senha_valida, msg_senha = validar_senha(senha)
            if not senha_valida:
                return False, msg_senha

            senha_hash = hash_senha(senha)

            # CORREÇÃO: Simplificado para retornar apenas sucesso e mensagem
            cursor.execute(
                "{CALL supply_chain.sp_criar_usuario(?, ?, ?, ?, ?, ?, ?, ?, ?)}",
                nome, sobrenome, data_nascimento, cpf_limpo, funcao, email, senha_hash, criado_por, pyodbc.SQL_PARAM_OUTPUT
            )
            self.conn.commit()
            return True, "Usuário criado com sucesso!"
        except Exception as e:
            self.conn.rollback()
            return False, f"Erro ao criar usuário: {e}"
        finally:
            cursor.close()
            self.desconectar()

    def autenticar(self, email: str, senha: str) -> Tuple[bool, str, Optional[str]]:
        """Autentica um usuário e retorna seu nível de acesso."""
        self.conectar()
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT id, hashed_senha, funcao, ativo, bloqueado_ate FROM supply_chain.usuarios WHERE email = ?", email)
            user = cursor.fetchone()

            if not user:
                return False, "Usuário não encontrado.", None
            
            if not user.ativo:
                return False, "Usuário inativo.", None
            
            if user.bloqueado_ate and user.bloqueado_ate > datetime.now():
                 return False, f"Usuário bloqueado até {user.bloqueado_ate}.", None

            if verificar_senha(senha, user.hashed_senha):
                cursor.execute("{CALL supply_chain.sp_atualizar_ultimo_acesso(?)}", user.id)
                self.conn.commit()
                return True, "Autenticação bem-sucedida!", user.funcao
            else:
                cursor.execute("{CALL supply_chain.sp_registrar_login_falho(?)}", email)
                self.conn.commit()
                return False, "Senha incorreta.", None
        except Exception as e:
            return False, f"Erro de autenticação: {e}", None
        finally:
            cursor.close()
            self.desconectar()