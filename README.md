# 📦 Nexum Supply Chain - Backend

> Sistema inteligente de gerenciamento de cadeia de suprimentos com rastreabilidade em tempo real, cálculo automático de necessidade de compras e notificações inteligentes.

[![Azure](https://img.shields.io/badge/Azure-SQL_Database-0078D4?logo=microsoftazure)](https://azure.microsoft.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1.2-000000?logo=flask)](https://flask.palletsprojects.com)

---

## 🎯 Visão Geral

O **Nexum Supply Chain** resolve problemas críticos de gestão de estoque:

- ✅ **Centralização de Dados**: Todos os dados em uma única fonte de verdade
- ✅ **Rastreabilidade em Tempo Real**: Saiba onde cada peça está a qualquer momento
- ✅ **Cálculo Inteligente**: Algoritmo que prevê necessidade de compra
- ✅ **Alertas Automáticos**: Notificações quando estoque crítico
- ✅ **Dashboards Executivos**: Visualize KPIs em tempo real

---

## 🚀 Quick Start

### **1. Clone o Repositório**
```bash
git clone https://github.com/BBTS-Nexum/Nexum-BackEnd.git
cd Nexum-BackEnd
```

### **2. Instale as Dependências**
```bash
pip install -r requirements.txt
```

### **3. Configure o Banco de Dados**
📖 Siga o guia completo: **[SETUP_DATABASE.md](SETUP_DATABASE.md)**

```bash
# Configure suas credenciais
cp .env.example .env
notepad .env

# Execute os scripts SQL no Azure Data Studio
# 1. database/create_table.sql
# 2. database/insert_data.sql
```

### **4. Execute a Aplicação**
```bash
python app.py
```

Acesse: http://localhost:5000

---

## 📊 Dados e Análise

### **Dados de Entrada**
O sistema processa dados de uma planilha CSV com **5.000 produtos**, contendo:
- Classificação ABC (Alto/Médio/Baixo valor)
- Estoque atual em múltiplas localizações
- Movimentações em trânsito
- Peças em teste, reparo e manutenção
- Consumo médio mensal (CMM)
- Coeficiente de perda

### **Problemas Identificados**
Nossa análise revelou:
- 🔴 **58.4%** dos produtos **sem estoque**
- 🟡 **100 produtos críticos** (alto CMM, sem estoque)
- 🟠 Apenas **2.4%** têm compras provisionadas
- 🔵 **70.038 peças** imobilizadas em testes/reparos

📈 Execute `python analise_dados.py` para ver análise completa

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────┐
│         Frontend (Web Dashboard / Mobile)       │
└─────────────────┬───────────────────────────────┘
                  │ REST API
┌─────────────────▼───────────────────────────────┐
│              Flask API Backend                   │
│  • Autenticação (Azure AD B2C)                  │
│  • Endpoints CRUD                                │
│  • Cálculo de Necessidade de Compra             │
│  • WebSockets (Tempo Real)                       │
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────┼─────────┬─────────────┐
        │         │         │             │
┌───────▼──┐ ┌───▼────┐ ┌──▼──────┐ ┌────▼────┐
│Azure SQL │ │Service │ │  Blob   │ │Functions│
│Database  │ │  Bus   │ │ Storage │ │         │
└──────────┘ └────────┘ └─────────┘ └─────────┘
```

---

## 📁 Estrutura do Projeto

```
Nexum-BackEnd/
├── app.py                      # Aplicação principal Flask
├── analise_dados.py            # Script de análise de dados
├── requirements.txt            # Dependências Python
├── .env.example                # Template de configuração
├── .gitignore                  # Arquivos ignorados pelo Git
│
├── database/                   # Scripts e docs do banco de dados
│   ├── create_table.sql        # Criação de tabelas, views, SPs
│   ├── insert_data.py          # Script Python para inserção
│   ├── generate_inserts.py     # Gerador de INSERTs SQL
│   ├── insert_data.sql         # INSERTs gerados (não commitado)
│   └── README.md               # Documentação do banco
│
├── dados_hackathon.csv         # Dados de entrada (5.000 produtos)
├── SETUP_DATABASE.md           # Guia de setup do banco
└── README.md                   # Este arquivo
```

---

## 🗄️ Banco de Dados

### **Tabela Principal**
`supply_chain.produtos_estoque` - Controle completo de estoque

### **Views Disponíveis**
1. `vw_produtos_criticos` - Produtos com risco de ruptura
2. `vw_dashboard_executivo` - KPIs gerenciais
3. `vw_analise_abc` - Análise por classificação

### **Stored Procedures**
1. `sp_calcular_necessidade_compra` - Cálculo inteligente de compras

### **Queries Úteis**

```sql
-- Ver produtos críticos
SELECT * FROM supply_chain.vw_produtos_criticos
WHERE nivel_criticidade = 'CRÍTICO';

-- Calcular necessidade de compra (30 dias, fator 1.5)
EXEC supply_chain.sp_calcular_necessidade_compra 
  @lead_time_dias = 30,
  @fator_seguranca = 1.5;

-- Dashboard executivo
SELECT * FROM supply_chain.vw_dashboard_executivo;
```

📖 **Documentação completa:** [database/README.md](database/README.md)

---

## 🔧 Tecnologias

### **Backend**
- **Python 3.11+**
- **Flask 3.1.2** - Framework web
- **PyODBC** - Conexão com Azure SQL
- **Pandas & NumPy** - Análise de dados

### **Database**
- **Azure SQL Database** - Banco de dados em nuvem
- **T-SQL** - Stored Procedures e Views

### **Azure Services (Planejado)**
- **Azure Service Bus** - Mensageria
- **Azure Functions** - Serverless computing
- **Azure Blob Storage** - Armazenamento de arquivos
- **Azure SignalR** - Comunicação em tempo real
- **Azure Container Apps** - Deploy e hosting

---

## 🎯 Funcionalidades

### ✅ **Implementado**
- [x] Análise completa de dados CSV
- [x] Estrutura de banco de dados otimizada
- [x] Views para dashboards
- [x] Stored procedure para cálculo de compras
- [x] Script de importação de dados
- [x] Documentação completa

### 🚧 **Em Desenvolvimento**
- [ ] API REST completa (FastAPI)
- [ ] Autenticação com Azure AD B2C
- [ ] Sistema de rastreabilidade
- [ ] Integração com Azure Service Bus
- [ ] Notificações inteligentes
- [ ] Dashboard web
- [ ] App mobile para scanning

### 📋 **Planejado**
- [ ] Machine Learning para previsão de demanda
- [ ] Integração com Power BI
- [ ] Geração automática de relatórios
- [ ] API de rastreamento com QR Code
- [ ] Sistema de workflows (Azure Logic Apps)

---

## 📈 KPIs e Métricas

O sistema calcula automaticamente:

| Métrica | Descrição |
|---------|-----------|
| **Taxa de Ruptura** | % de produtos sem estoque |
| **Produtos Críticos** | Itens com alta demanda sem estoque |
| **Necessidade de Compra** | Quantidade a ser comprada por produto |
| **Giro de Estoque** | Velocidade de movimentação |
| **CMM (Consumo Médio Mensal)** | Criticidade do produto |
| **Tempo em Trânsito** | Duração média de movimentação |

---

## 🔐 Segurança

- ✅ Variáveis de ambiente para credenciais
- ✅ `.env` no .gitignore
- ✅ Conexão criptografada com Azure SQL
- ✅ Trigger de auditoria automático
- 🚧 Azure AD B2C (em desenvolvimento)
- 🚧 Azure Key Vault (planejado)

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit suas mudanças: `git commit -m 'Add: nova funcionalidade'`
4. Push para a branch: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

---

## 📝 Licença

Este projeto está sob a licença especificada no arquivo [LICENSE](LICENSE).

---

## 👥 Equipe

**BBTS Nexum Team**
- GitHub: [@BBTS-Nexum](https://github.com/BBTS-Nexum)

---

## 📞 Suporte

- 📧 Email: [criar email do projeto]
- 📚 Wiki: [Em breve]
- 🐛 Issues: [GitHub Issues](https://github.com/BBTS-Nexum/Nexum-BackEnd/issues)

---

## 🎓 Recursos e Documentação

- [Azure SQL Database Docs](https://docs.microsoft.com/en-us/azure/azure-sql/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Python Best Practices](https://docs.python-guide.org/)
- [Supply Chain Management Concepts](https://www.investopedia.com/terms/s/scm.asp)

---

<div align="center">

**Desenvolvido com ❤️ pela equipe BBTS Nexum**

⭐ **Se este projeto te ajudou, deixe uma estrela!** ⭐

</div>
