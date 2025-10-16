-- ============================================================================
-- CRIAÇÃO DE TABELA DE USUÁRIOS - NEXUM SUPPLY CHAIN
-- Database: Nexum Supply Chain Management
-- Criado em: 2025-10-15
-- ============================================================================

-- Usar o mesmo schema supply_chain
USE [nexum-supply-chain-db];
GO

-- ============================================================================
-- TABELA: usuarios
-- Armazena dados de usuários do sistema
-- ============================================================================
IF OBJECT_ID('supply_chain.usuarios', 'U') IS NOT NULL
    DROP TABLE supply_chain.usuarios
GO

CREATE TABLE supply_chain.usuarios (
    -- Chave primária
    id INT IDENTITY(1,1) PRIMARY KEY,
    
    -- Dados pessoais
    nome NVARCHAR(100) NOT NULL,
    sobrenome NVARCHAR(100) NOT NULL,
    data_nascimento DATE NOT NULL,
    cpf CHAR(11) NOT NULL UNIQUE,  -- Armazenar apenas números
    
    -- Dados profissionais
    funcao NVARCHAR(50) NOT NULL,  -- Ex: 'admin', 'analista', 'operador', 'gerente'
    
    -- Credenciais
    email NVARCHAR(255) NOT NULL UNIQUE,
    hashed_senha NVARCHAR(255) NOT NULL,  -- Hash bcrypt da senha
    
    -- Controle de acesso
    ativo BIT NOT NULL DEFAULT 1,
    ultimo_acesso DATETIME2 NULL,
    tentativas_login_falhadas INT NOT NULL DEFAULT 0,
    bloqueado_ate DATETIME2 NULL,
    
    -- Auditoria
    data_criacao DATETIME2 NOT NULL DEFAULT GETDATE(),
    data_atualizacao DATETIME2 NOT NULL DEFAULT GETDATE(),
    criado_por INT NULL,
    atualizado_por INT NULL,
    
    -- Constraints
    CONSTRAINT CK_usuarios_funcao CHECK (funcao IN ('admin', 'analista', 'operador', 'gerente', 'visualizador')),
    CONSTRAINT CK_usuarios_cpf_valido CHECK (LEN(cpf) = 11 AND cpf NOT LIKE '%[^0-9]%'),
    CONSTRAINT CK_usuarios_email_valido CHECK (email LIKE '%_@__%.__%'),
    CONSTRAINT CK_usuarios_data_nascimento CHECK (data_nascimento < GETDATE()),
    CONSTRAINT CK_usuarios_tentativas CHECK (tentativas_login_falhadas >= 0),
    
    -- Foreign key para rastrear quem criou/atualizou
    CONSTRAINT FK_usuarios_criado_por FOREIGN KEY (criado_por) 
        REFERENCES supply_chain.usuarios(id),
    CONSTRAINT FK_usuarios_atualizado_por FOREIGN KEY (atualizado_por) 
        REFERENCES supply_chain.usuarios(id)
)
GO

-- ============================================================================
-- ÍNDICES PARA PERFORMANCE
-- ============================================================================

-- Índice para login (email é único e mais usado)
CREATE NONCLUSTERED INDEX IX_usuarios_email 
ON supply_chain.usuarios(email)
WHERE ativo = 1
GO

-- Índice para busca por CPF
CREATE NONCLUSTERED INDEX IX_usuarios_cpf 
ON supply_chain.usuarios(cpf)
WHERE ativo = 1
GO

-- Índice para busca por função
CREATE NONCLUSTERED INDEX IX_usuarios_funcao 
ON supply_chain.usuarios(funcao)
INCLUDE (nome, sobrenome, email, ativo)
GO

-- Índice para usuários ativos
CREATE NONCLUSTERED INDEX IX_usuarios_ativo 
ON supply_chain.usuarios(ativo, data_criacao DESC)
GO

-- ============================================================================
-- TRIGGER PARA ATUALIZAÇÃO AUTOMÁTICA
-- ============================================================================
CREATE OR ALTER TRIGGER supply_chain.TR_usuarios_update
ON supply_chain.usuarios
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE supply_chain.usuarios
    SET data_atualizacao = GETDATE()
    FROM supply_chain.usuarios u
    INNER JOIN inserted i ON u.id = i.id
END
GO

-- ============================================================================
-- VIEW: Usuários Ativos (sem senha)
-- ============================================================================
CREATE OR ALTER VIEW supply_chain.vw_usuarios_ativos
AS
SELECT 
    id,
    nome,
    sobrenome,
    nome + ' ' + sobrenome AS nome_completo,
    data_nascimento,
    DATEDIFF(YEAR, data_nascimento, GETDATE()) AS idade,
    cpf,
    -- Formatar CPF: 000.000.000-00
    STUFF(STUFF(STUFF(cpf, 10, 0, '-'), 7, 0, '.'), 4, 0, '.') AS cpf_formatado,
    funcao,
    email,
    ativo,
    ultimo_acesso,
    tentativas_login_falhadas,
    bloqueado_ate,
    CASE 
        WHEN bloqueado_ate IS NOT NULL AND bloqueado_ate > GETDATE() THEN 'BLOQUEADO'
        WHEN ativo = 0 THEN 'INATIVO'
        ELSE 'ATIVO'
    END AS status,
    data_criacao,
    data_atualizacao
FROM supply_chain.usuarios
WHERE ativo = 1
GO

-- ============================================================================
-- VIEW: Dashboard de Usuários
-- ============================================================================
CREATE OR ALTER VIEW supply_chain.vw_dashboard_usuarios
AS
SELECT 
    COUNT(*) AS total_usuarios,
    SUM(CASE WHEN ativo = 1 THEN 1 ELSE 0 END) AS usuarios_ativos,
    SUM(CASE WHEN ativo = 0 THEN 1 ELSE 0 END) AS usuarios_inativos,
    SUM(CASE WHEN bloqueado_ate > GETDATE() THEN 1 ELSE 0 END) AS usuarios_bloqueados,
    COUNT(DISTINCT funcao) AS total_funcoes,
    MAX(data_criacao) AS ultimo_cadastro,
    MAX(ultimo_acesso) AS ultimo_acesso_sistema
FROM supply_chain.usuarios
GO

-- ============================================================================
-- VIEW: Usuários por Função
-- ============================================================================
CREATE OR ALTER VIEW supply_chain.vw_usuarios_por_funcao
AS
SELECT 
    funcao,
    COUNT(*) AS total,
    SUM(CASE WHEN ativo = 1 THEN 1 ELSE 0 END) AS ativos,
    SUM(CASE WHEN ativo = 0 THEN 1 ELSE 0 END) AS inativos
FROM supply_chain.usuarios
GROUP BY funcao
GO

-- ============================================================================
-- STORED PROCEDURE: Criar Usuário
-- ============================================================================
CREATE OR ALTER PROCEDURE supply_chain.sp_criar_usuario
    @nome NVARCHAR(100),
    @sobrenome NVARCHAR(100),
    @data_nascimento DATE,
    @cpf CHAR(11),
    @funcao NVARCHAR(50),
    @email NVARCHAR(255),
    @hashed_senha NVARCHAR(255),
    @criado_por INT = NULL,
    @usuario_id INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Validar se CPF já existe
        IF EXISTS (SELECT 1 FROM supply_chain.usuarios WHERE cpf = @cpf)
        BEGIN
            RAISERROR('CPF já cadastrado no sistema.', 16, 1);
            RETURN;
        END
        
        -- Validar se email já existe
        IF EXISTS (SELECT 1 FROM supply_chain.usuarios WHERE email = @email)
        BEGIN
            RAISERROR('Email já cadastrado no sistema.', 16, 1);
            RETURN;
        END
        
        -- Inserir usuário
        INSERT INTO supply_chain.usuarios (
            nome, sobrenome, data_nascimento, cpf, funcao, 
            email, hashed_senha, criado_por, atualizado_por
        )
        VALUES (
            @nome, @sobrenome, @data_nascimento, @cpf, @funcao,
            @email, @hashed_senha, @criado_por, @criado_por
        );
        
        SET @usuario_id = SCOPE_IDENTITY();
        
        COMMIT TRANSACTION;
        
        -- Retornar dados do usuário criado (sem senha)
        SELECT 
            id, nome, sobrenome, email, funcao, data_criacao
        FROM supply_chain.usuarios
        WHERE id = @usuario_id;
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrorMessage, 16, 1);
    END CATCH
END
GO

-- ============================================================================
-- STORED PROCEDURE: Atualizar Último Acesso
-- ============================================================================
CREATE OR ALTER PROCEDURE supply_chain.sp_atualizar_ultimo_acesso
    @usuario_id INT
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE supply_chain.usuarios
    SET 
        ultimo_acesso = GETDATE(),
        tentativas_login_falhadas = 0
    WHERE id = @usuario_id;
END
GO

-- ============================================================================
-- STORED PROCEDURE: Registrar Login Falho
-- ============================================================================
CREATE OR ALTER PROCEDURE supply_chain.sp_registrar_login_falho
    @email NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @tentativas INT;
    DECLARE @usuario_id INT;
    
    -- Incrementar tentativas
    UPDATE supply_chain.usuarios
    SET tentativas_login_falhadas = tentativas_login_falhadas + 1
    WHERE email = @email;
    
    -- Verificar se deve bloquear (após 5 tentativas)
    SELECT 
        @tentativas = tentativas_login_falhadas,
        @usuario_id = id
    FROM supply_chain.usuarios
    WHERE email = @email;
    
    IF @tentativas >= 5
    BEGIN
        -- Bloquear por 30 minutos
        UPDATE supply_chain.usuarios
        SET bloqueado_ate = DATEADD(MINUTE, 30, GETDATE())
        WHERE id = @usuario_id;
        
        RETURN 1; -- Indica que usuário foi bloqueado
    END
    
    RETURN 0; -- Não bloqueado
END
GO

-- ============================================================================
-- STORED PROCEDURE: Desbloquear Usuário
-- ============================================================================
CREATE OR ALTER PROCEDURE supply_chain.sp_desbloquear_usuario
    @usuario_id INT,
    @admin_id INT
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE supply_chain.usuarios
    SET 
        bloqueado_ate = NULL,
        tentativas_login_falhadas = 0,
        atualizado_por = @admin_id
    WHERE id = @usuario_id;
    
    SELECT 
        id, nome, sobrenome, email, 
        'Usuário desbloqueado com sucesso' AS mensagem
    FROM supply_chain.usuarios
    WHERE id = @usuario_id;
END
GO

-- ============================================================================
-- STORED PROCEDURE: Alterar Senha
-- ============================================================================
CREATE OR ALTER PROCEDURE supply_chain.sp_alterar_senha
    @usuario_id INT,
    @nova_senha_hash NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE supply_chain.usuarios
    SET 
        hashed_senha = @nova_senha_hash,
        atualizado_por = @usuario_id
    WHERE id = @usuario_id;
    
    SELECT 'Senha alterada com sucesso' AS mensagem;
END
GO

-- ============================================================================
-- STORED PROCEDURE: Inativar Usuário
-- ============================================================================
CREATE OR ALTER PROCEDURE supply_chain.sp_inativar_usuario
    @usuario_id INT,
    @admin_id INT
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE supply_chain.usuarios
    SET 
        ativo = 0,
        atualizado_por = @admin_id
    WHERE id = @usuario_id;
    
    SELECT 
        id, nome, sobrenome, email, ativo,
        'Usuário inativado com sucesso' AS mensagem
    FROM supply_chain.usuarios
    WHERE id = @usuario_id;
END
GO

-- ============================================================================
-- FUNÇÃO: Validar CPF
-- ============================================================================
CREATE OR ALTER FUNCTION supply_chain.fn_validar_cpf(@cpf CHAR(11))
RETURNS BIT
AS
BEGIN
    -- Validação básica de CPF (apenas formato)
    IF LEN(@cpf) <> 11 OR @cpf LIKE '%[^0-9]%'
        RETURN 0;
    
    -- CPFs inválidos conhecidos (todos dígitos iguais)
    IF @cpf IN ('00000000000', '11111111111', '22222222222', '33333333333',
                '44444444444', '55555555555', '66666666666', '77777777777',
                '88888888888', '99999999999')
        RETURN 0;
    
    RETURN 1;
END
GO

-- ============================================================================
-- COMENTÁRIOS NA TABELA
-- ============================================================================
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Tabela de usuários do sistema Nexum Supply Chain', 
    @level0type = N'SCHEMA', @level0name = 'supply_chain',
    @level1type = N'TABLE',  @level1name = 'usuarios'
GO

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'CPF do usuário (apenas números, sem formatação)', 
    @level0type = N'SCHEMA', @level0name = 'supply_chain',
    @level1type = N'TABLE',  @level1name = 'usuarios',
    @level2type = N'COLUMN', @level2name = 'cpf'
GO

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Senha hasheada com bcrypt (nunca armazenar senha em texto plano)', 
    @level0type = N'SCHEMA', @level0name = 'supply_chain',
    @level1type = N'TABLE',  @level1name = 'usuarios',
    @level2type = N'COLUMN', @level2name = 'hashed_senha'
GO

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Função do usuário: admin, analista, operador, gerente, visualizador', 
    @level0type = N'SCHEMA', @level0name = 'supply_chain',
    @level1type = N'TABLE',  @level1name = 'usuarios',
    @level2type = N'COLUMN', @level2name = 'funcao'
GO

-- ============================================================================
-- INSERIR USUÁRIO ADMINISTRADOR PADRÃO
-- Senha: Admin@123 (trocar em produção!)
-- Hash bcrypt: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqK8fZ8l3m
-- ============================================================================
INSERT INTO supply_chain.usuarios (
    nome, sobrenome, data_nascimento, cpf, funcao, email, hashed_senha
)
VALUES (
    'Administrador',
    'Sistema',
    '1990-01-01',
    '00000000000',  -- CPF fictício - substituir em produção
    'admin',
    'admin@nexum.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqK8fZ8l3m'
);
GO

-- ============================================================================
PRINT '✅ Tabela supply_chain.usuarios criada com sucesso!'
PRINT '✅ Índices criados com sucesso!'
PRINT '✅ Trigger de auditoria criado com sucesso!'
PRINT '✅ Views criadas com sucesso!'
PRINT '✅ Stored Procedures criadas com sucesso!'
PRINT '✅ Usuário administrador padrão criado!'
PRINT ''
PRINT '📧 Login padrão: admin@nexum.com'
PRINT '🔑 Senha padrão: Admin@123'
PRINT '⚠️  IMPORTANTE: Trocar a senha em produção!'
PRINT ''
PRINT '📊 Estrutura de usuários pronta para uso!'
-- ============================================================================
