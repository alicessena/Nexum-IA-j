"""
Script para inserir dados do CSV no Azure SQL Database
Autor: Nexum Supply Chain Team
Data: 2025-10-15
"""

import pandas as pd
import pyodbc
from datetime import datetime
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# ============================================================================
# CONFIGURAÇÃO DE CONEXÃO COM AZURE SQL DATABASE
# ============================================================================
# Substitua com suas credenciais do Azure SQL Database
# Ou use variáveis de ambiente (recomendado)
AZURE_SQL_CONFIG = {
    'server': os.getenv('AZURE_SQL_SERVER', 'seu-servidor.database.windows.net'),
    'database': os.getenv('AZURE_SQL_DATABASE', 'nexum-supply-chain'),
    'username': os.getenv('AZURE_SQL_USERNAME', 'seu-usuario'),
    'password': os.getenv('AZURE_SQL_PASSWORD', 'sua-senha'),
    'driver': '{ODBC Driver 18 for SQL Server}'
}

def get_connection_string():
    """Gera a string de conexão para o Azure SQL Database"""
    return (
        f"DRIVER={AZURE_SQL_CONFIG['driver']};"
        f"SERVER={AZURE_SQL_CONFIG['server']};"
        f"DATABASE={AZURE_SQL_CONFIG['database']};"
        f"UID={AZURE_SQL_CONFIG['username']};"
        f"PWD={AZURE_SQL_CONFIG['password']};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )

def connect_to_database():
    """Estabelece conexão com o banco de dados"""
    try:
        conn_str = get_connection_string()
        conn = pyodbc.connect(conn_str)
        print("✅ Conexão estabelecida com sucesso!")
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco de dados: {e}")
        raise

def load_csv_data(csv_path='dados_hackathon.csv'):
    """Carrega dados do CSV"""
    try:
        df = pd.read_csv(csv_path, delimiter=';')
        print(f"✅ CSV carregado: {len(df)} registros encontrados")
        return df
    except Exception as e:
        print(f"❌ Erro ao carregar CSV: {e}")
        raise

def insert_data_batch(conn, df, batch_size=1000):
    """
    Insere dados em lotes para melhor performance
    """
    cursor = conn.cursor()
    total_inserted = 0
    total_records = len(df)
    
    # Query de inserção
    insert_query = """
    INSERT INTO supply_chain.produtos_estoque (
        codigo, abc, tipo, saldo_manut, provid_compras, recebimento_esperado,
        transito_manut, stage_manut, recepcao_manut, pendente_ri,
        pecas_teste_kit, pecas_teste, fornecedor_reparo, laboratorio,
        wr, wrcr, stage_wr, cmm, coef_perda
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    try:
        print(f"\n📤 Iniciando inserção de {total_records} registros...")
        print(f"   Tamanho do lote: {batch_size}")
        
        # Processar em lotes
        for i in range(0, total_records, batch_size):
            batch = df.iloc[i:i+batch_size]
            batch_data = []
            
            for _, row in batch.iterrows():
                batch_data.append((
                    row['codigo'],
                    row['abc'],
                    int(row['tipo']),
                    int(row['saldo_manut']),
                    int(row['provid_compras']),
                    int(row['recebimento_esperado']),
                    int(row['transito_manut']),
                    int(row['stage_manut']),
                    int(row['recepcao_manut']),
                    int(row['pendente_ri']),
                    int(row['pecas_teste_kit']),
                    int(row['pecas_teste']),
                    int(row['fornecedor_reparo']),
                    int(row['laboratorio']),
                    int(row['wr']),
                    int(row['wrcr']),
                    int(row['stage_wr']),
                    float(row['cmm']),
                    float(row['coef_perda'])
                ))
            
            # Executar batch insert
            cursor.executemany(insert_query, batch_data)
            conn.commit()
            
            total_inserted += len(batch_data)
            progress = (total_inserted / total_records) * 100
            print(f"   Progresso: {total_inserted}/{total_records} ({progress:.1f}%)")
        
        print(f"\n✅ Inserção concluída! Total: {total_inserted} registros")
        return total_inserted
        
    except Exception as e:
        print(f"\n❌ Erro durante inserção: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def verify_insertion(conn):
    """Verifica se os dados foram inseridos corretamente"""
    cursor = conn.cursor()
    
    try:
        print("\n🔍 Verificando inserção...")
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM supply_chain.produtos_estoque")
        count = cursor.fetchone()[0]
        print(f"   Total de registros na tabela: {count}")
        
        # Estatísticas básicas
        cursor.execute("""
            SELECT 
                abc,
                COUNT(*) as quantidade,
                SUM(saldo_manut) as estoque_total,
                AVG(cmm) as cmm_medio
            FROM supply_chain.produtos_estoque
            GROUP BY abc
            ORDER BY abc
        """)
        
        print("\n📊 Estatísticas por classificação ABC:")
        for row in cursor.fetchall():
            print(f"   Classe {row.abc}: {row.quantidade} produtos | "
                  f"Estoque: {row.estoque_total} | CMM médio: {row.cmm_medio:.2f}")
        
        # Produtos críticos
        cursor.execute("""
            SELECT COUNT(*) 
            FROM supply_chain.produtos_estoque 
            WHERE cmm > 1 AND saldo_manut = 0
        """)
        criticos = cursor.fetchone()[0]
        print(f"\n🚨 Produtos críticos (CMM > 1 e estoque = 0): {criticos}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante verificação: {e}")
        return False
    finally:
        cursor.close()

def clear_table(conn):
    """Limpa a tabela antes de inserir novos dados"""
    cursor = conn.cursor()
    try:
        print("\n🗑️  Limpando tabela existente...")
        cursor.execute("DELETE FROM supply_chain.produtos_estoque")
        conn.commit()
        print("✅ Tabela limpa com sucesso!")
    except Exception as e:
        print(f"⚠️  Aviso ao limpar tabela: {e}")
    finally:
        cursor.close()

def main():
    """Função principal"""
    print("=" * 80)
    print("🚀 IMPORTAÇÃO DE DADOS - NEXUM SUPPLY CHAIN")
    print("=" * 80)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. Carregar CSV
        df = load_csv_data('dados_hackathon.csv')
        
        # 2. Conectar ao banco
        conn = connect_to_database()
        
        # 3. Limpar tabela (opcional - descomente se quiser limpar antes)
        # clear_table(conn)
        
        # 4. Inserir dados
        total_inserted = insert_data_batch(conn, df, batch_size=1000)
        
        # 5. Verificar inserção
        verify_insertion(conn)
        
        # 6. Fechar conexão
        conn.close()
        
        print("\n" + "=" * 80)
        print("✅ PROCESSO CONCLUÍDO COM SUCESSO!")
        print("=" * 80)
        
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ ERRO NO PROCESSO: {e}")
        print("=" * 80)
        raise

if __name__ == "__main__":
    main()
