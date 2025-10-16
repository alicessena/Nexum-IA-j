"""
Gerenciador de Usuários - Nexum Supply Chain
Autor: BBTS Nexum Team
Data: 2025-10-15
"""

import pyodbc
import bcrypt
import re
from datetime import datetime, date
from typing import Optional, Dict, List
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONFIGURAÇÃO DE CONEXÃO
# ============================================================================
AZURE_SQL_CONFIG = {
    'server': os.getenv('AZURE_SQL_SERVER', 'seu-servidor.database.windows.net'),
    'database': os.getenv('AZURE_SQL_DATABASE', 'nexum-supply-chain'),
    'username': os.getenv('AZURE_SQL_USERNAME', 'seu-usuario'),
    'password': os.getenv('AZURE_SQL_PASSWORD', 'sua-senha'),
    'driver': '{ODBC Driver 18 for SQL Server}'
}

def get_connection():
    """Estabelece conexão com o banco de dados"""
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

# ============================================================================
# FUNÇÕES DE VALIDAÇÃO
# ============================================================================

def validar_cpf(cpf: str) -> bool:
    """
    Valida CPF (apenas números)
    """
    # Remover caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Verificar se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verificar se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Validação dos dígitos verificadores
    def calcular_digito(cpf_parcial):
        soma = sum(int(cpf_parcial[i]) * (len(cpf_parcial) + 1 - i) for i in range(len(cpf_parcial)))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto
    
    # Validar primeiro dígito
    if int(cpf[9]) != calcular_digito(cpf[:9]):
        return False
    
    # Validar segundo dígito
    if int(cpf[10]) != calcular_digito(cpf[:10]):
        return False
    
    return True

def validar_email(email: str) -> bool:
    """Valida formato de email"""
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(padrao, email))

def validar_senha(senha: str) -> tuple:
    """
    Valida força da senha
    Retorna: (bool, mensagem)
    """
    if len(senha) < 8:
        return False, "Senha deve ter no mínimo 8 caracteres"
    
    if not re.search(r'[A-Z]', senha):
        return False, "Senha deve conter pelo menos uma letra maiúscula"
    
    if not re.search(r'[a-z]', senha):
        return False, "Senha deve conter pelo menos uma letra minúscula"
    
    if not re.search(r'[0-9]', senha):
        return False, "Senha deve conter pelo menos um número"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
        return False, "Senha deve conter pelo menos um caractere especial"
    
    return True, "Senha válida"

def formatar_cpf(cpf: str) -> str:
    """Formata CPF: 000.000.000-00"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

def limpar_cpf(cpf: str) -> str:
    """Remove formatação do CPF"""
    return re.sub(r'[^0-9]', '', cpf)

# ============================================================================
# FUNÇÕES DE HASH DE SENHA
# ============================================================================

def hash_senha(senha: str) -> str:
    """Gera hash bcrypt da senha"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    """Verifica se a senha corresponde ao hash"""
    return bcrypt.checkpw(senha.encode('utf-8'), hash_armazenado.encode('utf-8'))

# ============================================================================
# CLASS: GerenciadorUsuarios
# ============================================================================

class GerenciadorUsuarios:
    """Gerencia operações de usuários no banco de dados"""
    
    FUNCOES_VALIDAS = ['admin', 'analista', 'operador', 'gerente', 'visualizador']
    
    def __init__(self):
        self.conn = None
    
    def conectar(self):
        """Estabelece conexão com o banco"""
        self.conn = get_connection()
    
    def desconectar(self):
        """Fecha conexão com o banco"""
        if self.conn:
            self.conn.close()
    
    def criar_usuario(
        self,
        nome: str,
        sobrenome: str,
        data_nascimento: date,
        cpf: str,
        funcao: str,
        email: str,
        senha: str,
        criado_por: Optional[int] = None
    ) -> Dict:
        """
        Cria um novo usuário no sistema
        """
        # Validações
        cpf_limpo = limpar_cpf(cpf)
        
        if not validar_cpf(cpf_limpo):
            raise ValueError("CPF inválido")
        
        if not validar_email(email):
            raise ValueError("Email inválido")
        
        senha_valida, mensagem_senha = validar_senha(senha)
        if not senha_valida:
            raise ValueError(mensagem_senha)
        
        if funcao.lower() not in self.FUNCOES_VALIDAS:
            raise ValueError(f"Função inválida. Use: {', '.join(self.FUNCOES_VALIDAS)}")
        
        # Hash da senha
        senha_hash = hash_senha(senha)
        
        # Executar stored procedure
        cursor = self.conn.cursor()
        
        try:
            # Preparar parâmetros
            usuario_id_output = cursor.execute(
                """
                DECLARE @usuario_id INT;
                EXEC supply_chain.sp_criar_usuario
                    @nome = ?,
                    @sobrenome = ?,
                    @data_nascimento = ?,
                    @cpf = ?,
                    @funcao = ?,
                    @email = ?,
                    @hashed_senha = ?,
                    @criado_por = ?,
                    @usuario_id = @usuario_id OUTPUT;
                SELECT @usuario_id;
                """,
                nome, sobrenome, data_nascimento, cpf_limpo, 
                funcao.lower(), email.lower(), senha_hash, criado_por
            ).fetchone()
            
            self.conn.commit()
            
            # Buscar dados do usuário criado
            usuario = self.buscar_usuario_por_email(email)
            
            return {
                'sucesso': True,
                'mensagem': 'Usuário criado com sucesso',
                'usuario': usuario
            }
            
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Erro ao criar usuário: {str(e)}")
        finally:
            cursor.close()
    
    def buscar_usuario_por_email(self, email: str) -> Optional[Dict]:
        """Busca usuário por email (sem retornar senha)"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                id, nome, sobrenome, data_nascimento, cpf, funcao,
                email, ativo, ultimo_acesso, tentativas_login_falhadas,
                bloqueado_ate, data_criacao
            FROM supply_chain.usuarios
            WHERE email = ?
        """, email.lower())
        
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            return None
        
        return {
            'id': row.id,
            'nome': row.nome,
            'sobrenome': row.sobrenome,
            'nome_completo': f"{row.nome} {row.sobrenome}",
            'data_nascimento': row.data_nascimento,
            'cpf': formatar_cpf(row.cpf),
            'funcao': row.funcao,
            'email': row.email,
            'ativo': bool(row.ativo),
            'ultimo_acesso': row.ultimo_acesso,
            'tentativas_login_falhadas': row.tentativas_login_falhadas,
            'bloqueado_ate': row.bloqueado_ate,
            'data_criacao': row.data_criacao
        }
    
    def autenticar(self, email: str, senha: str) -> Optional[Dict]:
        """
        Autentica usuário
        Retorna dados do usuário se autenticado, None caso contrário
        """
        cursor = self.conn.cursor()
        
        # Buscar usuário com senha
        cursor.execute("""
            SELECT 
                id, nome, sobrenome, funcao, email, hashed_senha,
                ativo, bloqueado_ate, tentativas_login_falhadas
            FROM supply_chain.usuarios
            WHERE email = ?
        """, email.lower())
        
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            return None
        
        # Verificar se usuário está ativo
        if not row.ativo:
            cursor.close()
            raise Exception("Usuário inativo")
        
        # Verificar se está bloqueado
        if row.bloqueado_ate and row.bloqueado_ate > datetime.now():
            cursor.close()
            raise Exception(f"Usuário bloqueado até {row.bloqueado_ate}")
        
        # Verificar senha
        if not verificar_senha(senha, row.hashed_senha):
            # Registrar login falho
            cursor.execute("EXEC supply_chain.sp_registrar_login_falho @email = ?", email.lower())
            self.conn.commit()
            cursor.close()
            raise Exception("Senha incorreta")
        
        # Atualizar último acesso
        cursor.execute("EXEC supply_chain.sp_atualizar_ultimo_acesso @usuario_id = ?", row.id)
        self.conn.commit()
        
        cursor.close()
        
        return {
            'id': row.id,
            'nome': row.nome,
            'sobrenome': row.sobrenome,
            'nome_completo': f"{row.nome} {row.sobrenome}",
            'funcao': row.funcao,
            'email': row.email
        }
    
    def alterar_senha(self, usuario_id: int, senha_atual: str, nova_senha: str) -> Dict:
        """Altera senha do usuário"""
        cursor = self.conn.cursor()
        
        # Buscar hash da senha atual
        cursor.execute("""
            SELECT hashed_senha, email
            FROM supply_chain.usuarios
            WHERE id = ?
        """, usuario_id)
        
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            raise Exception("Usuário não encontrado")
        
        # Verificar senha atual
        if not verificar_senha(senha_atual, row.hashed_senha):
            cursor.close()
            raise Exception("Senha atual incorreta")
        
        # Validar nova senha
        senha_valida, mensagem = validar_senha(nova_senha)
        if not senha_valida:
            cursor.close()
            raise ValueError(mensagem)
        
        # Gerar novo hash
        novo_hash = hash_senha(nova_senha)
        
        # Atualizar senha
        cursor.execute("""
            EXEC supply_chain.sp_alterar_senha 
                @usuario_id = ?,
                @nova_senha_hash = ?
        """, usuario_id, novo_hash)
        
        self.conn.commit()
        cursor.close()
        
        return {
            'sucesso': True,
            'mensagem': 'Senha alterada com sucesso'
        }
    
    def listar_usuarios(self, apenas_ativos: bool = True) -> List[Dict]:
        """Lista todos os usuários"""
        cursor = self.conn.cursor()
        
        if apenas_ativos:
            query = "SELECT * FROM supply_chain.vw_usuarios_ativos ORDER BY nome"
        else:
            query = """
                SELECT 
                    id, nome, sobrenome, email, funcao, ativo,
                    data_criacao, ultimo_acesso
                FROM supply_chain.usuarios
                ORDER BY nome
            """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        
        usuarios = []
        for row in rows:
            usuarios.append({
                'id': row.id,
                'nome': row.nome,
                'sobrenome': row.sobrenome,
                'nome_completo': f"{row.nome} {row.sobrenome}",
                'email': row.email,
                'funcao': row.funcao,
                'ativo': bool(row.ativo) if hasattr(row, 'ativo') else True,
                'data_criacao': row.data_criacao,
                'ultimo_acesso': row.ultimo_acesso if hasattr(row, 'ultimo_acesso') else None
            })
        
        return usuarios

# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("🔐 GERENCIADOR DE USUÁRIOS - NEXUM SUPPLY CHAIN")
    print("=" * 80)
    
    gerenciador = GerenciadorUsuarios()
    
    try:
        # Conectar ao banco
        print("\n📡 Conectando ao banco de dados...")
        gerenciador.conectar()
        print("✅ Conectado com sucesso!")
        
        # Exemplo: Criar usuário
        print("\n👤 Criando usuário de teste...")
        usuario = gerenciador.criar_usuario(
            nome="João",
            sobrenome="Silva",
            data_nascimento=date(1995, 5, 15),
            cpf="12345678901",
            funcao="analista",
            email="joao.silva@nexum.com",
            senha="Senha@123"
        )
        print(f"✅ Usuário criado: {usuario['usuario']['nome_completo']}")
        
        # Exemplo: Autenticar
        print("\n🔑 Testando autenticação...")
        auth = gerenciador.autenticar("joao.silva@nexum.com", "Senha@123")
        print(f"✅ Autenticado: {auth['nome_completo']} ({auth['funcao']})")
        
        # Exemplo: Listar usuários
        print("\n📋 Listando usuários ativos...")
        usuarios = gerenciador.listar_usuarios()
        print(f"✅ Total: {len(usuarios)} usuários")
        for u in usuarios:
            print(f"   - {u['nome_completo']} ({u['email']}) - {u['funcao']}")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
    
    finally:
        gerenciador.desconectar()
        print("\n👋 Desconectado do banco de dados")
        print("=" * 80)
