#!/usr/bin/env python3
"""
用户密码重置工具
用法: python reset_user_password.py <username> <new_password>
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def get_db_connection():
    """获取数据库连接"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'Alex'),
        user=os.getenv('DB_USER', 'xuehanshuo'),
        password=os.getenv('DB_PASSWORD', 'xuehanshuo'),
        cursor_factory=RealDictCursor
    )


def hash_password(password: str) -> str:
    """生成密码哈希"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def reset_password(username: str, new_password: str):
    """重置用户密码"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 检查用户是否存在
                cursor.execute(
                    "SELECT id, username, email FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()

                if not user:
                    print(f"❌ 用户 '{username}' 不存在")
                    return False

                # 生成新密码哈希
                password_hash = hash_password(new_password)

                # 更新密码
                cursor.execute("""
                    UPDATE users 
                    SET password_hash = %s, updated_at = NOW() 
                    WHERE username = %s
                """, (password_hash, username))

                conn.commit()

                print(f"✅ 用户 '{username}' 密码重置成功")
                print(f"📧 邮箱: {user['email']}")
                print(f"🔑 新密码: {new_password}")
                print(f"🔒 哈希值: {password_hash}")

                return True

    except Exception as e:
        print(f"❌ 重置密码失败: {e}")
        return False


def list_users():
    """列出所有用户"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT username, email, role, status, created_at 
                    FROM users 
                    ORDER BY created_at DESC
                """)
                users = cursor.fetchall()

                print("\n📋 系统用户列表:")
                print("-" * 80)
                print(f"{'用户名':<20} {'邮箱':<30} {'角色':<10} {'状态':<10} {'创建时间'}")
                print("-" * 80)

                for user in users:
                    created = user['created_at'].strftime('%Y-%m-%d %H:%M')
                    print(
                        f"{user['username']:<20} {user['email']:<30} {user['role']:<10} {user['status']:<10} {created}")

                print("-" * 80)
                print(f"总计: {len(users)} 个用户")

    except Exception as e:
        print(f"❌ 获取用户列表失败: {e}")


def main():
    if len(sys.argv) == 1:
        print("🔧 用户密码管理工具")
        print("\n用法:")
        print("  python reset_user_password.py list                    # 列出所有用户")
        print("  python reset_user_password.py <username> <password>   # 重置密码")
        print("\n示例:")
        print("  python reset_user_password.py admin admin123         # 重置admin密码为admin123")
        print("  python reset_user_password.py testuser newpass123    # 重置testuser密码")
        return

    if len(sys.argv) == 2 and sys.argv[1] == 'list':
        list_users()
        return

    if len(sys.argv) != 3:
        print("❌ 参数错误")
        print("用法: python reset_user_password.py <username> <new_password>")
        print("或者: python reset_user_password.py list")
        sys.exit(1)

    username = sys.argv[1]
    new_password = sys.argv[2]

    if len(new_password) < 6:
        print("❌ 密码长度至少6个字符")
        sys.exit(1)

    reset_password(username, new_password)


if __name__ == "__main__":
    main()
