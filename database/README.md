# 🗄️ Database - Nexum Supply Chain

Este diretório contém todos os scripts relacionados ao banco de dados Azure SQL.

## 📁 Estrutura de Arquivos

```
database/
├── create_table.sql       # Cria tabela, índices, views e stored procedures
├── insert_data.py         # Script Python para inserir dados via PyODBC
├── generate_inserts.py    # Gera arquivo SQL com comandos INSERT
└── insert_data.sql        # Arquivo gerado com INSERTs (criado automaticamente)
```

## 🚀 Como Usar

### **Opção 1: Usando Python (Recomendado para volumes grandes)**

1. **Configure o ambiente:**
   ```powershell
   # Copie o .env.example para .env
   Copy-Item .env.example .env
   
   # Edite .env com suas credenciais do Azure SQL
   notepad .env
   ```

2. **Instale as dependências:**
   ```powershell
   pip install pyodbc pandas python-dotenv
   ```

3. **Execute a criação da tabela no Azure:**
   - Conecte-se ao Azure SQL Database usando Azure Data Studio ou SSMS
   - Execute o script `create_table.sql`

4. **Insira os dados:**
   ```powershell
   python database/insert_data.py
   ```

### **Opção 2: Usando SQL Puro**

1. **Gere o arquivo de INSERTs:**
   ```powershell
   python database/generate_inserts.py
   ```

2. **Execute os scripts no Azure:**
   - Execute `create_table.sql` primeiro
   - Execute `insert_data.sql` depois (arquivo gerado)

## 🔧 Pré-requisitos

### **1. Azure SQL Database**

Crie um banco de dados no Azure:

```bash
# Via Azure CLI
az sql server create \
  --name nexum-supply-chain-server \
  --resource-group nexum-rg \
  --location brazilsouth \
  --admin-user nexumadmin \
  --admin-password "SuaSenhaSegura123!"

az sql db create \
  --resource-group nexum-rg \
  --server nexum-supply-chain-server \
  --name nexum-supply-chain-db \
  --service-objective S0
```

### **2. Configurar Firewall**

Adicione seu IP às regras de firewall:

```bash
az sql server firewall-rule create \
  --resource-group nexum-rg \
  --server nexum-supply-chain-server \
  --name AllowMyIP \
  --start-ip-address SEU_IP \
  --end-ip-address SEU_IP
```

Ou permita serviços do Azure:

```bash
az sql server firewall-rule create \
  --resource-group nexum-rg \
  --server nexum-supply-chain-server \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### **3. ODBC Driver (para Python)**

**Windows:**
- Download: [Microsoft ODBC Driver 18 for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

**Linux/Mac:**
```bash
# Ubuntu/Debian
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Mac
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
HOMEBREW_NO_ENV_FILTERING=1 ACCEPT_EULA=Y brew install msodbcsql18
```

## 📊 Estrutura do Banco de Dados

### **Tabela Principal: `supply_chain.produtos_estoque`**

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | INT | Chave primária (auto-incremento) |
| `codigo` | NVARCHAR(50) | Código único do produto (SKU) |
| `abc` | CHAR(1) | Classificação ABC (A/B/C) |
| `tipo` | INT | Tipo de produto (10/19/20) |
| `saldo_manut` | INT | Estoque disponível em manutenção |
| `provid_compras` | INT | Compras provisionadas |
| `cmm` | DECIMAL(10,2) | Consumo Médio Mensal |
| `coef_perda` | DECIMAL(10,8) | Coeficiente de perda |
| ... | ... | ... |

### **Views Disponíveis:**

1. **`vw_produtos_criticos`** - Produtos com alto CMM e baixo estoque
2. **`vw_dashboard_executivo`** - KPIs e métricas gerenciais
3. **`vw_analise_abc`** - Análise por classificação ABC

### **Stored Procedures:**

1. **`sp_calcular_necessidade_compra`** - Calcula o que precisa ser comprado

Exemplo de uso:
```sql
-- Lead time de 45 dias e fator de segurança 2.0
EXEC supply_chain.sp_calcular_necessidade_compra 
  @lead_time_dias = 45,
  @fator_seguranca = 2.0
```

## 📈 Queries Úteis

### **1. Produtos Críticos**
```sql
SELECT * FROM supply_chain.vw_produtos_criticos
WHERE nivel_criticidade IN ('CRÍTICO', 'ALTO')
ORDER BY cmm DESC
```

### **2. Dashboard Executivo**
```sql
SELECT * FROM supply_chain.vw_dashboard_executivo
```

### **3. Análise ABC**
```sql
SELECT * FROM supply_chain.vw_analise_abc
ORDER BY abc
```

### **4. Top 10 Produtos com Maior CMM**
```sql
SELECT TOP 10
    codigo,
    abc,
    saldo_manut,
    cmm,
    CASE 
        WHEN saldo_manut = 0 THEN 'SEM ESTOQUE'
        WHEN saldo_manut < cmm THEN 'ESTOQUE BAIXO'
        ELSE 'OK'
    END AS status
FROM supply_chain.produtos_estoque
ORDER BY cmm DESC
```

### **5. Produtos com Necessidade Urgente de Compra**
```sql
SELECT 
    codigo,
    abc,
    saldo_manut,
    provid_compras,
    cmm,
    (cmm * 2 - saldo_manut - provid_compras) AS necessidade_compra
FROM supply_chain.produtos_estoque
WHERE 
    cmm > 10 
    AND (saldo_manut + provid_compras) < (cmm * 2)
ORDER BY cmm DESC
```

## 🔒 Segurança

- **NUNCA** commite o arquivo `.env` no Git
- Use **Azure Key Vault** para armazenar credenciais em produção
- Configure **Azure AD Authentication** ao invés de SQL Authentication
- Ative **Transparent Data Encryption (TDE)** no Azure SQL
- Configure **Auditing** e **Advanced Threat Protection**

## 📝 Logs e Monitoramento

O trigger `TR_produtos_estoque_update` registra automaticamente:
- Data e hora de cada atualização
- Usuário que realizou a alteração

Para consultar histórico:
```sql
SELECT 
    codigo,
    data_criacao,
    data_atualizacao,
    usuario_criacao,
    usuario_atualizacao
FROM supply_chain.produtos_estoque
ORDER BY data_atualizacao DESC
```

## 🆘 Troubleshooting

### **Erro: "Login failed for user"**
- Verifique as credenciais no arquivo `.env`
- Confirme que o usuário tem permissões no banco de dados

### **Erro: "Cannot open server"**
- Verifique as regras de firewall no Azure Portal
- Confirme que seu IP está autorizado

### **Erro: "ODBC Driver not found"**
- Instale o Microsoft ODBC Driver 18 for SQL Server
- Verifique se o driver está no PATH do sistema

### **Performance lenta na inserção**
- Aumente o `batch_size` em `insert_data.py`
- Desabilite índices temporariamente durante inserção massiva
- Use `BULK INSERT` para volumes muito grandes

## 📚 Documentação Adicional

- [Azure SQL Database Documentation](https://docs.microsoft.com/en-us/azure/azure-sql/)
- [PyODBC Documentation](https://github.com/mkleehammer/pyodbc/wiki)
- [SQL Server Best Practices](https://docs.microsoft.com/en-us/sql/sql-server/sql-server-best-practices)

## 🤝 Contribuindo

Para modificar a estrutura do banco:
1. Edite `create_table.sql`
2. Teste localmente ou em ambiente de dev
3. Crie migration scripts para produção
4. Documente as alterações neste README
