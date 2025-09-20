-- 用户管理系统数据库表结构
-- 创建时间: 2025-09-20

-- 1. 用户表 (users)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    
    -- 用户状态
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'suspended', 'inactive')),
    
    -- 角色 (user/admin)
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    
    -- 权限相关
    permission_granted_at TIMESTAMP,
    permission_expires_at TIMESTAMP,
    granted_by INTEGER REFERENCES users(id),
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    
    -- 索引
    CONSTRAINT users_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- 2. 权限申请表 (permission_requests)
CREATE TABLE permission_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 申请信息
    request_reason TEXT NOT NULL,
    requested_duration VARCHAR(20) NOT NULL CHECK (requested_duration IN ('1week', '1month', '3months', '6months', '1year')),
    additional_info TEXT,
    
    -- 审批状态
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    
    -- 审批相关
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP,
    reviewer_comments TEXT,
    approved_duration VARCHAR(20),
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. 用户会话表 (user_sessions) - 用于JWT token管理
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP DEFAULT NOW(),
    
    -- 会话信息
    ip_address INET,
    user_agent TEXT
);

-- 4. 审计日志表 (audit_logs) - 记录重要操作
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50), -- 'user', 'permission_request', etc.
    entity_id INTEGER,
    details JSONB,
    ip_address INET,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_permission_expires ON users(permission_expires_at);

CREATE INDEX idx_permission_requests_user_id ON permission_requests(user_id);
CREATE INDEX idx_permission_requests_status ON permission_requests(status);
CREATE INDEX idx_permission_requests_created_at ON permission_requests(created_at);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token_hash ON user_sessions(token_hash);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- 创建触发器：自动更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $func$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$func$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_permission_requests_updated_at BEFORE UPDATE ON permission_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入默认管理员用户 (密码: admin123)
-- 注意: 在生产环境中请修改默认密码
INSERT INTO users (username, email, password_hash, full_name, status, role, permission_granted_at)
VALUES (
    'admin',
    'admin@alex.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewF5O0/OkMrQpjRm', -- admin123 的bcrypt hash
    'System Administrator',
    'active',
    'admin',
    NOW()
);

-- 创建视图：用户权限状态概览
CREATE VIEW user_permissions_view AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.full_name,
    u.status,
    u.role,
    u.permission_granted_at,
    u.permission_expires_at,
    u.created_at,
    CASE 
        WHEN u.permission_expires_at IS NULL THEN 'no_permission'
        WHEN u.permission_expires_at > NOW() THEN 'active'
        ELSE 'expired'
    END AS permission_status,
    granter.username AS granted_by_username
FROM users u
LEFT JOIN users granter ON u.granted_by = granter.id
WHERE u.role = 'user';

-- 创建视图：权限申请概览
CREATE VIEW permission_requests_view AS
SELECT 
    pr.id,
    pr.user_id,
    u.username,
    u.email,
    u.full_name,
    pr.request_reason,
    pr.requested_duration,
    pr.status,
    pr.reviewed_by,
    reviewer.username AS reviewed_by_username,
    pr.reviewed_at,
    pr.reviewer_comments,
    pr.approved_duration,
    pr.created_at,
    pr.updated_at
FROM permission_requests pr
JOIN users u ON pr.user_id = u.id
LEFT JOIN users reviewer ON pr.reviewed_by = reviewer.id;

-- 6. 密码重置token表 (password_reset_tokens)
CREATE TABLE password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    ip_address INET
);

-- 创建索引提高查询性能
CREATE INDEX idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX idx_password_reset_tokens_expires ON password_reset_tokens(expires_at);
