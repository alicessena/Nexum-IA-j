import pandas as pd
import numpy as np

# Carregar dados
df = pd.read_csv('dados_hackathon.csv', delimiter=';')

print("=" * 80)
print("📊 ANÁLISE DOS DADOS DE SUPPLY CHAIN")
print("=" * 80)

# Informações básicas
print("\n1️⃣ INFORMAÇÕES GERAIS:")
print(f"   Total de registros: {len(df)}")
print(f"   Total de colunas: {len(df.columns)}")
print(f"   Total de produtos únicos: {df['codigo'].nunique()}")

# Estrutura das colunas
print("\n2️⃣ ESTRUTURA DAS COLUNAS:")
print(df.dtypes)

# Estatísticas descritivas
print("\n3️⃣ ESTATÍSTICAS DOS DADOS NUMÉRICOS:")
print(df.describe())

# Análise por classificação ABC
print("\n4️⃣ DISTRIBUIÇÃO POR CLASSIFICAÇÃO ABC:")
print(df['abc'].value_counts())
print(f"\n   A (Alto valor): {(df['abc'] == 'A').sum()} itens")
print(f"   B (Médio valor): {(df['abc'] == 'B').sum()} itens")
print(f"   C (Baixo valor): {(df['abc'] == 'C').sum()} itens")

# Análise por tipo
print("\n5️⃣ DISTRIBUIÇÃO POR TIPO:")
print(df['tipo'].value_counts())

# Análise de estoque
print("\n6️⃣ ANÁLISE DE ESTOQUE:")
print(f"   Saldo total em manutenção: {df['saldo_manut'].sum()}")
print(f"   Produtos com estoque > 0: {(df['saldo_manut'] > 0).sum()}")
print(f"   Produtos com estoque = 0: {(df['saldo_manut'] == 0).sum()}")
print(f"   Média de estoque: {df['saldo_manut'].mean():.2f}")
print(f"   Mediana de estoque: {df['saldo_manut'].median():.2f}")

# Análise de compras
print("\n7️⃣ ANÁLISE DE COMPRAS:")
print(f"   Total previsto em compras: {df['provid_compras'].sum()}")
print(f"   Produtos com compras previstas: {(df['provid_compras'] > 0).sum()}")
print(f"   Total em recebimento esperado: {df['recebimento_esperado'].sum()}")

# Análise de trânsito/movimentação
print("\n8️⃣ ANÁLISE DE MOVIMENTAÇÃO:")
print(f"   Em trânsito (manutenção): {df['transito_manut'].sum()}")
print(f"   Em stage (manutenção): {df['stage_manut'].sum()}")
print(f"   Em recepção (manutenção): {df['recepcao_manut'].sum()}")
print(f"   Pendente RI: {df['pendente_ri'].sum()}")

# Análise de peças em teste
print("\n9️⃣ ANÁLISE DE TESTES:")
print(f"   Peças em teste (kit): {df['pecas_teste_kit'].sum()}")
print(f"   Peças em teste: {df['pecas_teste'].sum()}")

# Análise de reparos
print("\n🔟 ANÁLISE DE REPAROS:")
print(f"   Em fornecedor para reparo: {df['fornecedor_reparo'].sum()}")
print(f"   Em laboratório: {df['laboratorio'].sum()}")

# Análise WR (Work Request)
print("\n1️⃣1️⃣ ANÁLISE DE WR (Work Request):")
print(f"   Total WR: {df['wr'].sum()}")
print(f"   Total WRCR: {df['wrcr'].sum()}")
print(f"   Em stage WR: {df['stage_wr'].sum()}")

# Análise CMM e Coeficiente de Perda
print("\n1️⃣2️⃣ ANÁLISE DE CRITICIDADE:")
print(f"   CMM médio: {df['cmm'].mean():.2f}")
print(f"   CMM máximo: {df['cmm'].max():.2f}")
print(f"   Coeficiente de perda médio: {df['coef_perda'].mean():.4f}")
print(f"   Produtos com coef_perda = 0: {(df['coef_perda'] == 0).sum()}")
print(f"   Produtos com coef_perda > 1: {(df['coef_perda'] > 1).sum()}")

# Identificar produtos críticos (alto CMM + baixo estoque)
print("\n1️⃣3️⃣ PRODUTOS CRÍTICOS (CMM > 1 E ESTOQUE = 0):")
criticos = df[(df['cmm'] > 1) & (df['saldo_manut'] == 0)]
print(f"   Total: {len(criticos)} produtos")
if len(criticos) > 0:
    print("\n   Top 10 mais críticos:")
    print(criticos.nlargest(10, 'cmm')[['codigo', 'abc', 'cmm', 'saldo_manut', 'provid_compras']])

# Produtos com alta demanda de compra
print("\n1️⃣4️⃣ PRODUTOS COM MAIOR DEMANDA DE COMPRA:")
print(df.nlargest(10, 'provid_compras')[['codigo', 'abc', 'tipo', 'saldo_manut', 'provid_compras']])

# Análise de valores nulos
print("\n1️⃣5️⃣ ANÁLISE DE DADOS FALTANTES:")
print(df.isnull().sum())

# Resumo do fluxo logístico total
print("\n1️⃣6️⃣ RESUMO DO FLUXO LOGÍSTICO TOTAL:")
fluxo_total = {
    'Estoque Disponível': df['saldo_manut'].sum(),
    'Compras Provisionadas': df['provid_compras'].sum(),
    'Recebimento Esperado': df['recebimento_esperado'].sum(),
    'Em Trânsito': df['transito_manut'].sum(),
    'Em Stage': df['stage_manut'].sum(),
    'Em Recepção': df['recepcao_manut'].sum(),
    'Em Testes': df['pecas_teste_kit'].sum() + df['pecas_teste'].sum(),
    'Em Reparo': df['fornecedor_reparo'].sum() + df['laboratorio'].sum(),
    'WR Total': df['wr'].sum(),
}

for key, value in fluxo_total.items():
    print(f"   {key}: {value}")

print("\n" + "=" * 80)
print("✅ ANÁLISE CONCLUÍDA!")
print("=" * 80)
