"""
数据库连接和操作
"""
import psycopg2
import psycopg2.extras
import os
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'Alex'),
    'user': os.getenv('DB_USER', 'xuehanshuo'),
    'password': os.getenv('DB_PASSWORD', 'xuehanshuo')
}


class DatabaseError(Exception):
    """数据库错误异常"""
    pass


@contextmanager
def get_db_connection():
    """数据库连接上下文管理器"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
    except psycopg2.Error as e:
        logger.error(f"数据库连接错误: {e}")
        if conn:
            conn.rollback()
        raise DatabaseError(f"数据库操作失败: {e}")
    finally:
        if conn:
            conn.close()


@contextmanager
def get_db_cursor(commit=True):
    """数据库游标上下文管理器"""
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise


class UserDatabase:
    """用户数据库操作类"""

    @staticmethod
    def create_user(username: str, email: str, password_hash: str, full_name: Optional[str] = None) -> int:
        """创建用户"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, status, role)
                VALUES (%s, %s, %s, %s, 'pending', 'user')
                RETURNING id;
            """, (username, email, password_hash, full_name))
            result = cursor.fetchone()
            return result['id'] if result else None

    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM users WHERE username = %s;
            """, (username,))
            return cursor.fetchone()

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取用户"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM users WHERE email = %s;
            """, (email,))
            return cursor.fetchone()

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM users WHERE id = %s;
            """, (user_id,))
            return cursor.fetchone()

    @staticmethod
    def update_user_login_time(user_id: int):
        """更新用户最后登录时间"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE users SET last_login = NOW() WHERE id = %s;
            """, (user_id,))

    @staticmethod
    def update_user(user_id: int, **kwargs) -> bool:
        """更新用户信息"""
        if not kwargs:
            return False

        set_clauses = []
        values = []

        for key, value in kwargs.items():
            if key in ['username', 'full_name', 'email', 'status', 'password_hash']:
                set_clauses.append(f"{key} = %s")
                values.append(value)

        if not set_clauses:
            return False

        values.append(user_id)

        with get_db_cursor() as cursor:
            cursor.execute(f"""
                UPDATE users SET {', '.join(set_clauses)}, updated_at = NOW()
                WHERE id = %s;
            """, values)
            return cursor.rowcount > 0

    @staticmethod
    def get_all_users(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取所有用户"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT u.id, u.username, u.email, u.full_name, u.status, u.role,
                       u.permission_granted_at, u.permission_expires_at, u.created_at, u.last_login,
                       CASE 
                           WHEN u.permission_expires_at IS NULL THEN '永久权限'
                           WHEN u.permission_expires_at > NOW() THEN '有效'
                           ELSE '已过期'
                       END as permission_status,
                       granted_by.username as granted_by_username
                FROM users u
                LEFT JOIN users granted_by ON u.granted_by = granted_by.id
                ORDER BY u.created_at DESC
                LIMIT %s OFFSET %s;
            """, (limit, offset))
            return cursor.fetchall()

    @staticmethod
    def delete_user(user_id: int) -> bool:
        """删除用户"""
        with get_db_cursor() as cursor:
            # 首先检查用户是否存在且不是管理员
            cursor.execute("""
                SELECT role FROM users WHERE id = %s;
            """, (user_id,))
            result = cursor.fetchone()

            if not result:
                return False  # 用户不存在

            if result['role'] == 'admin':
                return False  # 不能删除管理员

            # 在删除用户之前，将相关审计日志的user_id设置为NULL
            cursor.execute("""
                UPDATE audit_logs SET user_id = NULL 
                WHERE user_id = %s;
            """, (user_id,))

            # 删除用户的会话记录（有CASCADE约束，会自动删除）
            # 删除用户的权限申请记录（有CASCADE约束，会自动删除）

            # 最后删除用户
            cursor.execute("""
                DELETE FROM users WHERE id = %s;
            """, (user_id,))

            return cursor.rowcount > 0

    @staticmethod
    def update_user_permission(user_id: int, days: int, granted_by: int) -> bool:
        """更新用户权限时长"""
        with get_db_cursor() as cursor:
            if days == -1:  # 永久权限
                cursor.execute("""
                    UPDATE users 
                    SET permission_granted_at = NOW(),
                        permission_expires_at = NULL,
                        granted_by = %s,
                        status = 'active',
                        updated_at = NOW()
                    WHERE id = %s AND role = 'user';
                """, (granted_by, user_id))
            elif days == 0:  # 立即过期
                cursor.execute("""
                    UPDATE users 
                    SET permission_granted_at = NOW(),
                        permission_expires_at = NOW(),
                        granted_by = %s,
                        status = 'inactive',
                        updated_at = NOW()
                    WHERE id = %s AND role = 'user';
                """, (granted_by, user_id))
            else:  # 指定天数权限
                cursor.execute("""
                    UPDATE users 
                    SET permission_granted_at = NOW(),
                        permission_expires_at = NOW() + INTERVAL '%s days',
                        granted_by = %s,
                        status = 'active',
                        updated_at = NOW()
                    WHERE id = %s AND role = 'user';
                """, (days, granted_by, user_id))
            return cursor.rowcount > 0

    @staticmethod
    def update_password(user_id: int, password_hash: str) -> bool:
        """更新用户密码"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE users 
                SET password_hash = %s, updated_at = NOW()
                WHERE id = %s;
            """, (password_hash, user_id))
            return cursor.rowcount > 0

    @staticmethod
    def grant_permission(user_id: int, duration: str, granted_by: int) -> bool:
        """授予用户权限"""
        with get_db_cursor() as cursor:
            # 计算过期时间
            duration_map = {
                '1week': "INTERVAL '1 week'",
                '1month': "INTERVAL '1 month'",
                '3months': "INTERVAL '3 months'",
                '6months': "INTERVAL '6 months'",
                '1year': "INTERVAL '1 year'"
            }

            # 检查是否为预设值
            if duration in duration_map:
                interval_expr = duration_map[duration]
            else:
                # 检查是否为自定义天数格式 (如 "30days")
                import re
                match = re.match(r'^(\d+)days?$', duration)
                if match:
                    days = int(match.group(1))
                    interval_expr = f"INTERVAL '{days} days'"
                else:
                    raise ValueError(f"无效的权限时长: {duration}")

            cursor.execute(f"""
                UPDATE users 
                SET status = 'active',
                    permission_granted_at = NOW(),
                    permission_expires_at = NOW() + {interval_expr},
                    granted_by = %s
                WHERE id = %s;
            """, (granted_by, user_id))
            return cursor.rowcount > 0


class PermissionRequestDatabase:
    """权限申请数据库操作类"""

    @staticmethod
    def create_request(user_id: int, request_reason: str, requested_duration: str, additional_info: str = None) -> int:
        """创建权限申请"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO permission_requests (user_id, request_reason, requested_duration, additional_info)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """, (user_id, request_reason, requested_duration, additional_info))
            result = cursor.fetchone()
            return result['id'] if result else None

    @staticmethod
    def get_request_by_id(request_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取权限申请"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM permission_requests_view WHERE id = %s;
            """, (request_id,))
            return cursor.fetchone()

    @staticmethod
    def get_user_requests(user_id: int) -> List[Dict[str, Any]]:
        """获取用户的所有权限申请"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM permission_requests_view 
                WHERE user_id = %s 
                ORDER BY created_at DESC;
            """, (user_id,))
            return cursor.fetchall()

    @staticmethod
    def get_pending_requests() -> List[Dict[str, Any]]:
        """获取所有待审批的权限申请"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM permission_requests_view 
                WHERE status = 'pending' 
                ORDER BY created_at ASC;
            """)
            return cursor.fetchall()

    @staticmethod
    def get_all_requests(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取所有权限申请"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT * FROM permission_requests_view 
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s;
            """, (limit, offset))
            return cursor.fetchall()

    @staticmethod
    def review_request(request_id: int, approved: bool, reviewed_by: int,
                       reviewer_comments: Optional[str] = None,
                       approved_duration: Optional[str] = None) -> bool:
        """审批权限申请"""
        status = 'approved' if approved else 'rejected'

        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE permission_requests 
                SET status = %s, 
                    reviewed_by = %s, 
                    reviewed_at = NOW(),
                    reviewer_comments = %s,
                    approved_duration = %s
                WHERE id = %s;
            """, (status, reviewed_by, reviewer_comments, approved_duration, request_id))
            return cursor.rowcount > 0

    @staticmethod
    def delete_request(request_id: int) -> bool:
        """删除权限申请"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                DELETE FROM permission_requests WHERE id = %s;
            """, (request_id,))
            return cursor.rowcount > 0


class SessionDatabase:
    """用户会话数据库操作类"""

    @staticmethod
    def create_session(user_id: int, token_hash: str, expires_at, ip_address: str = None, user_agent: str = None):
        """创建用户会话"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_sessions (user_id, token_hash, expires_at, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s);
            """, (user_id, token_hash, expires_at, ip_address, user_agent))

    @staticmethod
    def validate_session(token_hash: str) -> Optional[Dict[str, Any]]:
        """验证会话token"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT s.*, u.id as user_id, u.username, u.email, u.role, u.status
                FROM user_sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token_hash = %s AND s.expires_at > NOW();
            """, (token_hash,))
            return cursor.fetchone()

    @staticmethod
    def delete_session(token_hash: str):
        """删除会话"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                DELETE FROM user_sessions WHERE token_hash = %s;
            """, (token_hash,))

    @staticmethod
    def cleanup_expired_sessions():
        """清理过期会话"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                DELETE FROM user_sessions WHERE expires_at <= NOW();
            """)


class AuditDatabase:
    """审计日志数据库操作类"""

    @staticmethod
    def log_action(user_id: Optional[int], action: str, entity_type: Optional[str] = None,
                   entity_id: Optional[int] = None, details: Optional[Dict] = None,
                   ip_address: Optional[str] = None):
        """记录审计日志"""
        import json
        with get_db_cursor() as cursor:
            # 将details字典转换为JSON字符串
            details_json = json.dumps(details) if details else None
            cursor.execute("""
                INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (user_id, action, entity_type, entity_id, details_json, ip_address))


class StatsDatabase:
    """统计信息数据库操作类"""

    @staticmethod
    def get_admin_stats() -> Dict[str, int]:
        """获取管理员统计信息"""
        try:
            with get_db_cursor(commit=False) as cursor:
                stats = {
                    'total_users': 0,
                    'admin_users': 0,
                    'pending_requests': 0,
                    'active_users': 0,
                    'expired_permissions': 0
                }

                # 总用户数
                try:
                    cursor.execute(
                        "SELECT COUNT(*) FROM users WHERE role = 'user';")
                    result = cursor.fetchone()
                    stats['total_users'] = int(
                        result['count']) if result else 0
                except:
                    stats['total_users'] = 0

                # 管理员数量
                try:
                    cursor.execute(
                        "SELECT COUNT(*) FROM users WHERE role = 'admin';")
                    result = cursor.fetchone()
                    stats['admin_users'] = int(
                        result['count']) if result else 0
                except:
                    stats['admin_users'] = 0

                # 待审批申请数
                try:
                    cursor.execute(
                        "SELECT COUNT(*) FROM permission_requests WHERE status = 'pending';")
                    result = cursor.fetchone()
                    stats['pending_requests'] = int(
                        result['count']) if result else 0
                except:
                    stats['pending_requests'] = 0

                # 活跃用户数
                try:
                    cursor.execute("""
                        SELECT COUNT(*) FROM users 
                        WHERE role = 'user' AND status = 'active' 
                        AND (permission_expires_at IS NULL OR permission_expires_at > NOW());
                    """)
                    result = cursor.fetchone()
                    stats['active_users'] = int(
                        result['count']) if result else 0
                except:
                    stats['active_users'] = 0

                # 过期权限数
                try:
                    cursor.execute("""
                        SELECT COUNT(*) FROM users 
                        WHERE role = 'user' AND permission_expires_at IS NOT NULL 
                        AND permission_expires_at <= NOW();
                    """)
                    result = cursor.fetchone()
                    stats['expired_permissions'] = int(
                        result['count']) if result else 0
                except:
                    stats['expired_permissions'] = 0

                return stats
        except Exception as e:
            print(f"Error in get_admin_stats: {e}")
            return {
                'total_users': 0,
                'admin_users': 0,
                'pending_requests': 0,
                'active_users': 0,
                'expired_permissions': 0
            }


class PasswordResetDatabase:
    """密码重置token数据库操作类"""

    @staticmethod
    def create_reset_token(user_id: int, token: str, ip_address: str = None) -> int:
        """创建密码重置token"""
        with get_db_cursor() as cursor:
            # 删除该用户的旧token
            cursor.execute("""
                DELETE FROM password_reset_tokens 
                WHERE user_id = %s OR expires_at < NOW();
            """, (user_id,))

            # 创建新token，24小时有效
            cursor.execute("""
                INSERT INTO password_reset_tokens (user_id, token, expires_at, ip_address)
                VALUES (%s, %s, NOW() + INTERVAL '24 hours', %s)
                RETURNING id;
            """, (user_id, token, ip_address))

            result = cursor.fetchone()
            return result['id'] if result else None

    @staticmethod
    def verify_reset_token(token: str) -> Dict[str, Any]:
        """验证重置token"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT rt.*, u.username, u.email 
                FROM password_reset_tokens rt
                JOIN users u ON rt.user_id = u.id
                WHERE rt.token = %s 
                AND rt.expires_at > NOW() 
                AND rt.used = FALSE;
            """, (token,))

            return cursor.fetchone()

    @staticmethod
    def mark_token_used(token: str) -> bool:
        """标记token为已使用"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE password_reset_tokens 
                SET used = TRUE 
                WHERE token = %s;
            """, (token,))

            return cursor.rowcount > 0

    @staticmethod
    def clean_expired_tokens():
        """清理过期的token"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                DELETE FROM password_reset_tokens 
                WHERE expires_at < NOW() OR used = TRUE;
            """)

            return cursor.rowcount
