import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from typing import List, Dict

# --- Configuração de Ambiente e Dados ---

# Tenta importar o serviço real. Caso falhe, usa a contingência.
try:
    from Nexum_BackEnd_main.stock import service_generate_acquisition_suggestion as obter_sugestoes_compra
    _LIVE_DB_MODE = True
except ImportError:
    _LIVE_DB_MODE = False
    
    def obter_sugestoes_compra() -> List[Dict]:
        """Contingência de dados local."""
        # Se for para o Hackathon/Teste, é crucial que este CSV esteja formatado corretamente.
        import pandas as pd
        CSV_PATH = "dados_hackathon.csv"
        MAX_CRITICOS = 5
        try:
            df = pd.read_csv(CSV_PATH, delimiter=';')
            
            # Recálculo de 'quantidade_a_comprar' e filtro de críticos
            df['quantidade_a_comprar'] = ((df['cmm'] * 2) - df['saldo_manut'] - df['provid_compras']).clip(lower=0)
            
            criticos = df[df['quantidade_a_comprar'] > 0].copy()
            
            # Mapeamento para o formato esperado pelo prompt do Gemini
            dados_sp = pd.DataFrame({
                'codigo': criticos['codigo'],
                'abc': criticos['abc'], # Mantido, mas não usado pelo Gemini neste prompt
                'estoque_atual': criticos['saldo_manut'],
                # IMPORTANTE: Para a regra INVESTIGAR, é bom incluir um estoque_maximo.
                # Como não está no CSV, vou forçar um valor alto para itens A/B de alto CMM.
                'estoque_maximo': criticos.apply(lambda row: 500 if row['cmm'] > 0.8 else 100, axis=1), 
                'cmm': criticos['cmm'],
                'compras_em_andamento': criticos['provid_compras'],
                'quantidade_a_comprar': criticos['quantidade_a_comprar'],
            })
            
            # Prioriza os X com maior CMM
            return dados_sp.nlargest(MAX_CRITICOS, 'cmm').to_dict('records')
        except FileNotFoundError:
            print("ERRO: Arquivo dados_hackathon.csv não encontrado.")
            return []


load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"

try:
    if not GEMINI_API_KEY:
        raise ValueError("Chave GEMINI_API_KEY não encontrada no .env")
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"ERRO DE CONFIGURAÇÃO: {e}")
    client = None

# --- Funções do Agente de IA ---

def percepcao_critica_db_call() -> List[Dict]:
    """Acessa o serviço de aquisição ou contingência."""
    if _LIVE_DB_MODE:
        print("📡 PERCEPÇÃO: Chamando serviço REAL do stock.py...")
    else:
        print("📡 PERCEPÇÃO: Executando contingência de dados...")
        
    return obter_sugestoes_compra()

def raciocinar_e_planejar_real(dados_criticos: List[Dict]) -> str:
    """Envia dados ao Gemini para gerar o plano de compra."""
    if not client:
        return json.dumps({"erro": "Cliente Gemini não inicializado."})
    
    # Instrução de sistema aprimorada para garantir a precisão da IA
    instrucao_sistema = """
Você é o **Agente de Automação de Compras (AAC)** da Nexum, com total **autoridade** para emitir ordens de compra.
Sua única saída é um **PLANO DE COMPRA** no formato JSON, conforme o schema.

### Lógica de Decisão Rigorosa
1. **Priorização:** Analise e ordene os itens pelo maior **CMM**, depois pela maior **quantidade_a_comprar**.
2. **ACÃO FINAL:** Determine a ação com base nos seguintes critérios:
    * **'ENVIAR ORDEM DE COMPRA':** Se `quantidade_a_comprar` for maior que 0.
    * **'INVESTIGAR DEMANDA':** Se o `CMM` for **acima de 0.8** E o `estoque_atual` for **90% ou mais** do `estoque_maximo`.
    * **'MONITORAR':** Para todos os outros casos (onde não há necessidade de compra).

### Formato de Saída (JSON Estruturado)
O JSON deve ser um array de objetos, onde cada objeto representa a ação para um produto:

```json
[
  {
    "codigo": "[Código do item]",
    "acao_sugerida": "[ACÃO FINAL determinada]",
    "quantidade_acao": [quantidade_a_comprar, ou 0 se for INVESTIGAR/MONITORAR],
    "justificativa_curta": "[Comentário: Compra, Alto CMM/Estoque, ou Monitorar.]"
  }
]
"""

    prompt_usuario = f"""
DADOS CRÍTICOS (JSON):
{json.dumps(dados_criticos, indent=2)}

Gere o plano de ação rigoroso em JSON, listando os itens na ordem de prioridade.
"""
    
    # Esquema de saída simplificado e direto
    schema_saida = types.Schema(
        type=types.Type.ARRAY,
        description="Plano de ação rigoroso e ordenado por prioridade (CMM > Quantidade).",
        items=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "codigo": types.Schema(type=types.Type.STRING),
                "acao_sugerida": types.Schema(type=types.Type.STRING, description="Ação Final: ENVIAR ORDEM DE COMPRA, INVESTIGAR DEMANDA, ou MONITORAR."),
                "quantidade_acao": types.Schema(type=types.Type.NUMBER, description="A quantidade para a ação (compra) ou 0."),
                "justificativa_curta": types.Schema(type=types.Type.STRING),
            }
        )
    )
    
    config = types.GenerateContentConfig(
        system_instruction=instrucao_sistema,
        response_mime_type="application/json",
        response_schema=schema_saida,
    )

    print("🧠 RACIOCÍNIO: Enviando dados para o Agente de IA (Gemini)...")
    
    response = client.models.generate_content(
        model=MODEL_NAME, 
        contents=[prompt_usuario],
        config=config
    )
    
    print("✅ RACIOCÍNIO CONCLUÍDO.")
    return response.text

def executar_plano_real(plano_json: str):
    """Processa a saída e simula a execução no ERP."""
    try:
        plano = json.loads(plano_json)
    except json.JSONDecodeError:
        print("\n❌ ERRO: A resposta do Agente não é um JSON válido.")
        return

    print("\n==================================================")
    print("🚀 AÇÃO EXECUTADA (Orquestração de Compras)")
    print("==================================================")
    
    if not plano:
        print("Nenhuma ação a ser executada pelo plano.")
        return

    # O item de maior prioridade é sempre o primeiro do array
    print(f"📢 Item de Maior Prioridade: {plano[0].get('codigo')}")
    print(f"   Ação Prioritária: {plano[0].get('acao_sugerida')}")
    print("--------------------------------------------------")

    for item in plano:
        codigo = item['codigo']
        acao = item['acao_sugerida'].upper()
        qtd = item['quantidade_acao']
        
        if "ENVIAR ORDEM DE COMPRA" in acao:
            print(f"   [ORDEM CRIADA]: {codigo} -> QTD: {qtd:.0f} | Status: {acao}.")
        elif "INVESTIGAR" in acao:
            print(f"   [ALERTA ENVIADO]: {codigo} -> Status: {acao}.")
        else:
            print(f"   [MONITORAR]: {codigo} -> Ação: {acao}.")

    print("==================================================")
    print("✅ CICLO DO AGENTE DE IA CONCLUÍDO.")
    print("==================================================")


if __name__ == "__main__":
    if not client:
        print("Agente de IA não pode ser executado devido a erro de inicialização.")
    else:
        dados_criticos_reais = percepcao_critica_db_call()
        
        if dados_criticos_reais:
            plano_json_real = raciocinar_e_planejar_real(dados_criticos_reais)
            executar_plano_real(plano_json_real)
        else:
            print("Nenhuma sugestão de compra encontrada. O Agente não gerou ações.")