"""
Gerador de Scripts SQL INSERT a partir do CSV
Cria um arquivo .sql com todos os comandos INSERT prontos para executar
"""

import pandas as pd

def escape_sql_string(value):
    """Escapa aspas simples em strings SQL"""
    if isinstance(value, str):
        return value.replace("'", "''")
    return value

def generate_insert_statements(csv_path='dados_hackathon.csv', output_path='database/insert_data.sql'):
    """
    Gera arquivo SQL com comandos INSERT para todos os registros do CSV
    """
    print("🔄 Carregando dados do CSV...")
    df = pd.read_csv(csv_path, delimiter=';')
    
    total_records = len(df)
    print(f"✅ {total_records} registros carregados")
    
    print(f"\n📝 Gerando script SQL...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Cabeçalho
        f.write("-- ============================================================================\n")
        f.write("-- SCRIPT DE INSERÇÃO DE DADOS - NEXUM SUPPLY CHAIN\n")
        f.write(f"-- Total de registros: {total_records}\n")
        f.write("-- Gerado automaticamente a partir de dados_hackathon.csv\n")
        f.write("-- ============================================================================\n\n")
        
        f.write("SET NOCOUNT ON;\n")
        f.write("GO\n\n")
        
        f.write("BEGIN TRANSACTION;\n")
        f.write("GO\n\n")
        
        f.write("PRINT 'Iniciando inserção de dados...';\n")
        f.write("GO\n\n")
        
        # Gerar INSERTs em lotes de 1000 (limite do SQL Server)
        batch_size = 1000
        batch_count = 0
        
        for i in range(0, total_records, batch_size):
            batch = df.iloc[i:i+batch_size]
            batch_count += 1
            
            f.write(f"-- Lote {batch_count} ({len(batch)} registros)\n")
            f.write("INSERT INTO supply_chain.produtos_estoque\n")
            f.write("    (codigo, abc, tipo, saldo_manut, provid_compras, recebimento_esperado,\n")
            f.write("     transito_manut, stage_manut, recepcao_manut, pendente_ri,\n")
            f.write("     pecas_teste_kit, pecas_teste, fornecedor_reparo, laboratorio,\n")
            f.write("     wr, wrcr, stage_wr, cmm, coef_perda)\n")
            f.write("VALUES\n")
            
            values = []
            for idx, row in batch.iterrows():
                value_str = (
                    f"    ('{escape_sql_string(row['codigo'])}', "
                    f"'{row['abc']}', "
                    f"{int(row['tipo'])}, "
                    f"{int(row['saldo_manut'])}, "
                    f"{int(row['provid_compras'])}, "
                    f"{int(row['recebimento_esperado'])}, "
                    f"{int(row['transito_manut'])}, "
                    f"{int(row['stage_manut'])}, "
                    f"{int(row['recepcao_manut'])}, "
                    f"{int(row['pendente_ri'])}, "
                    f"{int(row['pecas_teste_kit'])}, "
                    f"{int(row['pecas_teste'])}, "
                    f"{int(row['fornecedor_reparo'])}, "
                    f"{int(row['laboratorio'])}, "
                    f"{int(row['wr'])}, "
                    f"{int(row['wrcr'])}, "
                    f"{int(row['stage_wr'])}, "
                    f"{row['cmm']}, "
                    f"{row['coef_perda']})"
                )
                values.append(value_str)
            
            f.write(",\n".join(values))
            f.write(";\n")
            f.write("GO\n\n")
            
            # Adicionar checkpoint a cada 10 lotes
            if batch_count % 10 == 0:
                f.write(f"PRINT 'Processados {i + len(batch)} de {total_records} registros...';\n")
                f.write("GO\n\n")
        
        # Rodapé
        f.write("\nPRINT 'Verificando inserção...';\n")
        f.write("GO\n\n")
        
        f.write("SELECT COUNT(*) AS total_registros FROM supply_chain.produtos_estoque;\n")
        f.write("GO\n\n")
        
        f.write("COMMIT TRANSACTION;\n")
        f.write("GO\n\n")
        
        f.write("PRINT '✅ Inserção concluída com sucesso!';\n")
        f.write("GO\n")
    
    print(f"✅ Script SQL gerado: {output_path}")
    print(f"📊 Total de lotes: {batch_count}")
    print(f"📊 Total de registros: {total_records}")
    print(f"\n💡 Para executar no Azure SQL Database:")
    print(f"   1. Abra o Azure Data Studio ou SQL Server Management Studio")
    print(f"   2. Conecte-se ao seu banco de dados")
    print(f"   3. Abra e execute o arquivo: {output_path}")

if __name__ == "__main__":
    generate_insert_statements()
