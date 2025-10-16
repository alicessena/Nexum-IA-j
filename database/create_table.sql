-- ============================================================================
-- CRIAÇÃO DE TABELA PARA SUPPLY CHAIN - AZURE SQL DATABASE
-- Database: Nexum Supply Chain Management
-- Criado em: 2025-10-15
-- ============================================================================

-- Criar schema se não existir
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'supply_chain')
BEGIN
    EXEC('CREATE SCHEMA supply_chain')
END
GO

-- Dropar tabela se existir (apenas para desenvolvimento)
IF OBJECT_ID('supply_chain.produtos_estoque', 'U') IS NOT NULL
    DROP TABLE supply_chain.produtos_estoque
GO

-- ============================================================================
-- TABELA PRINCIPAL: produtos_estoque
-- Armazena todos os dados de produtos, estoque e movimentações
-- ============================================================================
CREATE TABLE supply_chain.produtos_estoque (
    -- Chave primária e identificação
    id INT IDENTITY(1,1) PRIMARY KEY,
    codigo NVARCHAR(50) NOT NULL UNIQUE,
    
    -- Classificação do produto
    abc CHAR(1) NOT NULL CHECK (abc IN ('A', 'B', 'C')),
    tipo INT NOT NULL CHECK (tipo IN (10, 19, 20)),
    
    -- Estoque e compras
    saldo_manut INT NOT NULL DEFAULT 0,
    provid_compras INT NOT NULL DEFAULT 0,
    recebimento_esperado INT NOT NULL DEFAULT 0,
    
    -- Movimentações e localização
    transito_manut INT NOT NULL DEFAULT 0,
    stage_manut INT NOT NULL DEFAULT 0,
    recepcao_manut INT NOT NULL DEFAULT 0,
    pendente_ri INT NOT NULL DEFAULT 0,
    
    -- Testes e qualidade
    pecas_teste_kit INT NOT NULL DEFAULT 0,
    pecas_teste INT NOT NULL DEFAULT 0,
    
    -- Reparos
    fornecedor_reparo INT NOT NULL DEFAULT 0,
    laboratorio INT NOT NULL DEFAULT 0,
    
    -- Work Requests
    wr INT NOT NULL DEFAULT 0,
    wrcr INT NOT NULL DEFAULT 0,
    stage_wr INT NOT NULL DEFAULT 0,
    
    -- Métricas e KPIs
    cmm DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    coef_perda DECIMAL(10,8) NOT NULL DEFAULT 0.00000000,
    
    -- Auditoria e controle
    data_criacao DATETIME2 NOT NULL DEFAULT GETDATE(),
    data_atualizacao DATETIME2 NOT NULL DEFAULT GETDATE(),
    usuario_criacao NVARCHAR(100) DEFAULT SYSTEM_USER,
    usuario_atualizacao NVARCHAR(100) DEFAULT SYSTEM_USER,
    ativo BIT NOT NULL DEFAULT 1,
    
    -- Constraints e índices
    CONSTRAINT CK_saldo_manut_positivo CHECK (saldo_manut >= 0),
    CONSTRAINT CK_cmm_positivo CHECK (cmm >= 0),
    CONSTRAINT CK_coef_perda_range CHECK (coef_perda >= 0)
)
GO

-- ============================================================================
-- ÍNDICES PARA PERFORMANCE
-- ============================================================================

-- Índice para busca por classificação ABC
CREATE NONCLUSTERED INDEX IX_produtos_estoque_abc 
ON supply_chain.produtos_estoque(abc) 
INCLUDE (codigo, saldo_manut, cmm)
GO

-- Índice para busca por tipo
CREATE NONCLUSTERED INDEX IX_produtos_estoque_tipo 
ON supply_chain.produtos_estoque(tipo)
GO

-- Índice para produtos críticos (alto CMM, baixo estoque)
CREATE NONCLUSTERED INDEX IX_produtos_estoque_criticos 
ON supply_chain.produtos_estoque(cmm DESC, saldo_manut ASC)
WHERE saldo_manut = 0 AND cmm > 1
GO

-- Índice para produtos com estoque
CREATE NONCLUSTERED INDEX IX_produtos_estoque_com_saldo 
ON supply_chain.produtos_estoque(saldo_manut)
WHERE saldo_manut > 0
GO

-- Índice para data de atualização (queries de auditoria)
CREATE NONCLUSTERED INDEX IX_produtos_estoque_data_atualizacao 
ON supply_chain.produtos_estoque(data_atualizacao DESC)
GO

-- ============================================================================
-- TRIGGER PARA ATUALIZAÇÃO AUTOMÁTICA DE DATA
-- ============================================================================
CREATE OR ALTER TRIGGER supply_chain.TR_produtos_estoque_update
ON supply_chain.produtos_estoque
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE supply_chain.produtos_estoque
    SET 
        data_atualizacao = GETDATE(),
        usuario_atualizacao = SYSTEM_USER
    FROM supply_chain.produtos_estoque pe
    INNER JOIN inserted i ON pe.id = i.id
END
GO

-- ============================================================================
-- VIEW PARA PRODUTOS CRÍTICOS
-- ============================================================================
CREATE OR ALTER VIEW supply_chain.vw_produtos_criticos
AS
SELECT 
    codigo,
    abc,
    tipo,
    saldo_manut,
    provid_compras,
    cmm,
    coef_perda,
    -- Cálculo de criticidade
    CASE 
        WHEN cmm > 100 AND saldo_manut = 0 THEN 'CRÍTICO'
        WHEN cmm > 50 AND saldo_manut = 0 THEN 'ALTO'
        WHEN cmm > 10 AND saldo_manut = 0 THEN 'MÉDIO'
        WHEN cmm > 1 AND saldo_manut = 0 THEN 'BAIXO'
        ELSE 'OK'
    END AS nivel_criticidade,
    -- Cálculo de necessidade de compra (Lead time de 30 dias)
    CAST(
        (cmm * 2) -- Estoque de segurança (2 meses)
        - saldo_manut 
        - provid_compras 
        - transito_manut 
        - recebimento_esperado 
        AS INT
    ) AS necessidade_compra,
    data_atualizacao
FROM supply_chain.produtos_estoque
WHERE ativo = 1 AND cmm > 0
GO

-- ============================================================================
-- VIEW PARA DASHBOARD EXECUTIVO
-- ============================================================================
CREATE OR ALTER VIEW supply_chain.vw_dashboard_executivo
AS
SELECT 
    -- Totalizadores
    COUNT(*) AS total_produtos,
    COUNT(DISTINCT abc) AS total_classes_abc,
    SUM(saldo_manut) AS estoque_total,
    SUM(provid_compras) AS compras_provisionadas,
    SUM(transito_manut) AS total_em_transito,
    SUM(pecas_teste_kit + pecas_teste) AS total_em_teste,
    SUM(fornecedor_reparo + laboratorio) AS total_em_reparo,
    SUM(wr) AS total_wr,
    
    -- Métricas
    AVG(cmm) AS cmm_medio,
    AVG(coef_perda) AS coef_perda_medio,
    
    -- Produtos sem estoque
    SUM(CASE WHEN saldo_manut = 0 THEN 1 ELSE 0 END) AS produtos_sem_estoque,
    
    -- Taxa de ruptura
    CAST(
        SUM(CASE WHEN saldo_manut = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
        AS DECIMAL(5,2)
    ) AS taxa_ruptura_percentual,
    
    -- Produtos críticos
    SUM(CASE WHEN cmm > 1 AND saldo_manut = 0 THEN 1 ELSE 0 END) AS produtos_criticos,
    
    -- Última atualização
    MAX(data_atualizacao) AS ultima_atualizacao
FROM supply_chain.produtos_estoque
WHERE ativo = 1
GO

-- ============================================================================
-- VIEW PARA ANÁLISE ABC
-- ============================================================================
CREATE OR ALTER VIEW supply_chain.vw_analise_abc
AS
SELECT 
    abc,
    COUNT(*) AS quantidade_produtos,
    SUM(saldo_manut) AS estoque_total,
    AVG(saldo_manut) AS estoque_medio,
    SUM(provid_compras) AS compras_provisionadas,
    AVG(cmm) AS cmm_medio,
    SUM(CASE WHEN saldo_manut = 0 THEN 1 ELSE 0 END) AS produtos_sem_estoque,
    CAST(
        SUM(CASE WHEN saldo_manut = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
        AS DECIMAL(5,2)
    ) AS taxa_ruptura_percentual
FROM supply_chain.produtos_estoque
WHERE ativo = 1
GROUP BY abc
GO

-- ============================================================================
-- STORED PROCEDURE: Calcular Necessidade de Compra
-- ============================================================================
CREATE OR ALTER PROCEDURE supply_chain.sp_calcular_necessidade_compra
    @lead_time_dias INT = 30,
    @fator_seguranca DECIMAL(5,2) = 1.5
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        codigo,
        abc,
        saldo_manut AS estoque_atual,
        provid_compras AS compras_em_andamento,
        cmm,
        
        -- Demanda prevista no lead time
        CAST((cmm * @lead_time_dias / 30.0) AS INT) AS demanda_lead_time,
        
        -- Estoque de segurança
        CAST((cmm * @lead_time_dias / 30.0 * @fator_seguranca) AS INT) AS estoque_seguranca,
        
        -- Necessidade de compra
        CASE 
            WHEN (
                CAST((cmm * @lead_time_dias / 30.0 * @fator_seguranca) AS INT)
                - saldo_manut 
                - provid_compras 
                - transito_manut
            ) > 0 
            THEN (
                CAST((cmm * @lead_time_dias / 30.0 * @fator_seguranca) AS INT)
                - saldo_manut 
                - provid_compras 
                - transito_manut
            )
            ELSE 0
        END AS quantidade_a_comprar,
        
        -- Prioridade
        CASE 
            WHEN cmm > 100 AND saldo_manut = 0 THEN 1
            WHEN cmm > 50 AND saldo_manut < (cmm * 0.5) THEN 2
            WHEN cmm > 10 AND saldo_manut < cmm THEN 3
            ELSE 4
        END AS prioridade,
        
        data_atualizacao
    FROM supply_chain.produtos_estoque
    WHERE 
        ativo = 1 
        AND cmm > 0
        AND (
            saldo_manut + provid_compras + transito_manut 
            < (cmm * @lead_time_dias / 30.0 * @fator_seguranca)
        )
    ORDER BY prioridade ASC, cmm DESC
END
GO

-- ============================================================================
-- COMENTÁRIOS NA TABELA E COLUNAS
-- ============================================================================
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Tabela principal de controle de estoque e movimentação de produtos', 
    @level0type = N'SCHEMA', @level0name = 'supply_chain',
    @level1type = N'TABLE',  @level1name = 'produtos_estoque'
GO

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Classificação ABC: A=Alto valor, B=Médio valor, C=Baixo valor', 
    @level0type = N'SCHEMA', @level0name = 'supply_chain',
    @level1type = N'TABLE',  @level1name = 'produtos_estoque',
    @level2type = N'COLUMN', @level2name = 'abc'
GO

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Consumo Médio Mensal - indica a criticidade do produto', 
    @level0type = N'SCHEMA', @level0name = 'supply_chain',
    @level1type = N'TABLE',  @level1name = 'produtos_estoque',
    @level2type = N'COLUMN', @level2name = 'cmm'
GO

-- ============================================================================
PRINT '✅ Tabela supply_chain.produtos_estoque criada com sucesso!'
PRINT '✅ Índices criados com sucesso!'
PRINT '✅ Trigger de auditoria criado com sucesso!'
PRINT '✅ Views criadas com sucesso!'
PRINT '✅ Stored Procedures criadas com sucesso!'
PRINT ''
PRINT '📊 Estrutura do banco de dados pronta para uso!'
-- ============================================================================
