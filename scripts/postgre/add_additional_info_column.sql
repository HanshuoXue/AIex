-- 为 permission_requests 表添加 additional_info 字段
-- 这个脚本用于更新现有数据库结构

-- 添加 additional_info 字段
ALTER TABLE permission_requests 
ADD COLUMN IF NOT EXISTS additional_info TEXT;

-- 更新视图以包含新字段
DROP VIEW IF EXISTS permission_requests_view;

CREATE VIEW permission_requests_view AS
SELECT 
    pr.id,
    pr.user_id,
    u.username,
    u.email,
    u.full_name,
    pr.request_reason,
    pr.requested_duration,
    pr.additional_info,
    pr.status,
    pr.reviewed_by,
    reviewer.username as reviewed_by_username,
    pr.reviewed_at,
    pr.reviewer_comments,
    pr.created_at,
    pr.updated_at
FROM permission_requests pr
JOIN users u ON pr.user_id = u.id
LEFT JOIN users reviewer ON pr.reviewed_by = reviewer.id;
