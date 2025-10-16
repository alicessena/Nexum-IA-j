# 🚀 Guia Rápido - Setup do Banco de Dados

## ⚡ Setup Rápido (5 minutos)

### **Passo 1: Criar Azure SQL Database**

#### Opção A: Via Portal Azure (Interface Gráfica)
1. Acesse: https://portal.azure.com
2. Clique em "Create a resource" → "Databases" → "SQL Database"
3. Preencha:
   - **Subscription**: Sua assinatura
   - **Resource Group**: Crie "nexum-rg"
   - **Database name**: nexum-supply-chain-db
   - **Server**: Criar novo
     - Server name: nexum-supply-chain-server
     - Location: Brazil South
     - Authentication: SQL authentication
     - Login: nexumadmin
     - Password: [sua senha segura]
   - **Compute + storage**: Basic (5 DTUs) - Para desenvolvimento
4. Clique em "Review + Create" → "Create"

#### Opção B: Via Azure CLI (Linha de Comando)
```bash
# Login no Azure
az login

# Criar resource group
az group create --name nexum-rg --location brazilsouth

# Criar SQL Server
az sql server create \
  --name nexum-supply-chain-server \
  --resource-group nexum-rg \
  --location brazilsouth \
  --admin-user nexumadmin \
  --admin-password "SuaSenhaSegura123!"

# Criar banco de dados
az sql db create \
  --resource-group nexum-rg \
  --server nexum-supply-chain-server \
  --name nexum-supply-chain-db \
  --service-objective Basic

# Permitir seu IP
az sql server firewall-rule create \
  --resource-group nexum-rg \
  --server nexum-supply-chain-server \
  --name AllowMyIP \
  --start-ip-address $(curl -s ifconfig.me) \
  --end-ip-address $(curl -s ifconfig.me)

# Permitir serviços Azure
az sql server firewall-rule create \
  --resource-group nexum-rg \
  --server nexum-supply-chain-server \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

---

### **Passo 2: Configurar Firewall**

No Portal Azure:
1. Vá para o SQL Server criado
2. "Security" → "Networking"
3. Marque "Allow Azure services and resources to access this server"
4. Adicione seu IP atual em "Firewall rules"
5. Salvar

---

### **Passo 3: Conectar e Executar Scripts**

#### **Opção 1: Azure Data Studio (Recomendado)**

1. **Download:** https://docs.microsoft.com/en-us/sql/azure-data-studio/download
2. **Instalar e abrir**
3. **Nova conexão:**
   - Connection type: Microsoft SQL Server
   - Server: `nexum-supply-chain-server.database.windows.net`
   - Authentication type: SQL Login
   - User name: `nexumadmin`
   - Password: [sua senha]
   - Database: `nexum-supply-chain-db`
   - Encrypt: Mandatory
4. **Connect**

5. **Executar scripts:**
   ```
   a) Abrir database/create_table.sql
   b) Clicar em "Run" (ou F5)
   c) Aguardar conclusão ✅
   
   d) Abrir database/insert_data.sql
   e) Clicar em "Run" (ou F5)
   f) Aguardar conclusão ✅ (pode demorar 1-2 minutos)
   ```

#### **Opção 2: SQL Server Management Studio (SSMS)**
1. **Download:** https://aka.ms/ssmsfullsetup
2. Mesmo processo do Azure Data Studio

#### **Opção 3: Via Python (Automático)**

1. **Configurar .env:**
   ```powershell
   Copy-Item .env.example .env
   notepad .env
   ```

2. **Preencher .env:**
   ```env
   AZURE_SQL_SERVER=nexum-supply-chain-server.database.windows.net
   AZURE_SQL_DATABASE=nexum-supply-chain-db
   AZURE_SQL_USERNAME=nexumadmin
   AZURE_SQL_PASSWORD=SuaSenhaSegura123!
   ```

3. **Executar:**
   ```powershell
   # Criar tabela primeiro (via Azure Data Studio)
   # Depois executar:
   python database/insert_data.py
   ```

---

### **Passo 4: Verificar Instalação**

Execute esta query no Azure Data Studio:

```sql
-- Verificar total de registros
SELECT COUNT(*) AS total_produtos 
FROM supply_chain.produtos_estoque;

-- Dashboard executivo
SELECT * FROM supply_chain.vw_dashboard_executivo;

-- Top 10 produtos críticos
SELECT TOP 10 * 
FROM supply_chain.vw_produtos_criticos
WHERE nivel_criticidade IN ('CRÍTICO', 'ALTO')
ORDER BY cmm DESC;
```

✅ **Sucesso!** Se você ver 5000 produtos, está tudo certo!

---

## 🔥 Queries Essenciais

### **1. Ver Produtos Críticos**
```sql
SELECT * FROM supply_chain.vw_produtos_criticos
WHERE nivel_criticidade = 'CRÍTICO'
ORDER BY cmm DESC;
```

### **2. Calcular Necessidade de Compra**
```sql
EXEC supply_chain.sp_calcular_necessidade_compra 
  @lead_time_dias = 30,
  @fator_seguranca = 1.5;
```

### **3. Análise por Classificação ABC**
```sql
SELECT * FROM supply_chain.vw_analise_abc;
```

### **4. Produtos Sem Estoque**
```sql
SELECT codigo, abc, cmm, provid_compras
FROM supply_chain.produtos_estoque
WHERE saldo_manut = 0 AND cmm > 10
ORDER BY cmm DESC;
```

---

## 🎯 Próximos Passos

Depois do banco configurado:

1. ✅ **Criar API REST** (FastAPI)
2. ✅ **Implementar autenticação** (Azure AD B2C)
3. ✅ **Criar endpoints** para rastreabilidade
4. ✅ **Integrar Azure Service Bus** para notificações
5. ✅ **Criar dashboard** (Power BI ou Web)
6. ✅ **Deploy no Azure** (Container Apps)

---

## 📞 Troubleshooting

### ❌ "Cannot open server"
**Solução:** Adicione seu IP no firewall do SQL Server

### ❌ "Login failed"
**Solução:** Verifique usuário e senha no .env

### ❌ "Database does not exist"
**Solução:** Execute create_table.sql primeiro

### ❌ "Object already exists"
**Solução:** Comente a linha `DROP TABLE` no create_table.sql

---

## 💰 Custos Estimados

**Banco de Dados (Basic tier):**
- ~R$ 30/mês
- Ideal para desenvolvimento e testes
- Limite: 2GB de armazenamento

**Produção (Standard S0):**
- ~R$ 100/mês
- Melhor performance
- Limite: 250GB de armazenamento

💡 **Dica:** Use Free Tier do Azure para estudantes!
https://azure.microsoft.com/free/students/

---

## 🎓 Recursos de Aprendizado

- [Azure SQL Database Tutorial](https://docs.microsoft.com/en-us/azure/azure-sql/database/single-database-create-quickstart)
- [SQL Server for Beginners](https://www.youtube.com/playlist?list=PLdo4fOcmZ0oX8qNdZ5hZWv0VtM9MqcHt5)
- [Azure Data Studio Guide](https://docs.microsoft.com/en-us/sql/azure-data-studio/)

---

**Pronto para começar! 🚀**
