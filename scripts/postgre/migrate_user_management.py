#!/usr/bin/env python3
"""
用户管理系统数据库迁移脚本
运行此脚本来创建用户管理相关的数据库表
"""

import psycopg2
import os
import sys
from datetime import datetime
import bcrypt

# 从环境变量读取数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'Alex'),
    'user': os.getenv('DB_USER', 'xuehanshuo'),
    'password': os.getenv('DB_PASSWORD', 'xuehanshuo')
}


def get_sql_content():
    """读取SQL文件内容"""
    sql_file_path = os.path.join(
        os.path.dirname(__file__), 'user_management.sql')
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"错误: 找不到SQL文件 {sql_file_path}")
        sys.exit(1)


def hash_password(password: str) -> str:
    """生成密码hash"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def split_sql_statements(sql_content):
    """智能分割SQL语句，正确处理函数定义中的分号"""
    statements = []
    current_statement = ""
    in_function = False
    in_dollar_quote = False
    dollar_quote_tag = None
    i = 0

    while i < len(sql_content):
        char = sql_content[i]

        # 检查是否进入或退出函数定义
        if not in_function and 'CREATE OR REPLACE FUNCTION' in current_statement.upper():
            in_function = True

        # 检查美元引号
        if char == '$' and not in_dollar_quote:
            # 查找美元引号标签
            j = i + 1
            while j < len(sql_content) and sql_content[j] != '$':
                j += 1
            if j < len(sql_content):
                dollar_quote_tag = sql_content[i:j+1]
                in_dollar_quote = True
                current_statement += char
                i += 1
                continue
        elif in_dollar_quote and char == '$':
            # 检查是否是结束的美元引号
            j = i
            while j < len(sql_content) and sql_content[j] != '$':
                j += 1
            if j < len(sql_content) and sql_content[i:j+1] == dollar_quote_tag:
                in_dollar_quote = False
                dollar_quote_tag = None
                current_statement += char
                i += 1
                continue

        current_statement += char

        # 检查语句结束
        if char == ';' and not in_dollar_quote:
            # 检查是否在函数定义中
            if in_function:
                # 检查是否到达函数定义的结尾
                if 'END;' in current_statement.upper() and 'LANGUAGE' in current_statement.upper():
                    statements.append(current_statement.strip())
                    current_statement = ""
                    in_function = False
            else:
                statements.append(current_statement.strip())
                current_statement = ""

        i += 1

    # 添加最后一个语句（如果有）
    if current_statement.strip():
        statements.append(current_statement.strip())

    return [stmt for stmt in statements if stmt.strip()]


def check_table_exists(cursor, table_name):
    """检查表是否存在"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        );
    """, (table_name,))
    return cursor.fetchone()[0]


def migrate_user_management():
    """执行用户管理系统数据库迁移"""

    print("=== 用户管理系统数据库迁移 ===")
    print(
        f"连接数据库: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")

    try:
        # 连接数据库
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("✓ 数据库连接成功")

        # 检查是否已存在用户表
        if check_table_exists(cursor, 'users'):
            print("⚠️  警告: users表已存在")
            # 在非交互式环境中自动继续
            import sys
            if sys.stdin.isatty():
                response = input("是否继续？这可能会覆盖现有数据。(y/N): ")
                if response.lower() != 'y':
                    print("取消迁移")
                    return
            else:
                print("非交互式环境，自动继续...")

            # 删除现有表（按依赖关系顺序）
            print("删除现有表...")
            drop_tables = [
                'DROP VIEW IF EXISTS permission_requests_view;',
                'DROP VIEW IF EXISTS user_permissions_view;',
                'DROP TABLE IF EXISTS audit_logs;',
                'DROP TABLE IF EXISTS user_sessions;',
                'DROP TABLE IF EXISTS permission_requests;',
                'DROP TABLE IF EXISTS users CASCADE;',
                'DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;'
            ]

            for drop_sql in drop_tables:
                cursor.execute(drop_sql)

            conn.commit()
            print("✓ 现有表已删除")

        # 读取并执行SQL
        sql_content = get_sql_content()

        print("执行数据库迁移...")

        # 智能分割SQL语句，处理函数定义中的分号
        statements = split_sql_statements(sql_content)

        for i, statement in enumerate(statements):
            try:
                if statement.strip():
                    cursor.execute(statement)
                    print(f"✓ 执行语句 {i+1}/{len(statements)}")
            except Exception as e:
                print(f"❌ 执行语句失败 {i+1}: {e}")
                print(f"语句: {statement[:100]}...")
                raise

        # 提交更改
        conn.commit()

        # 验证表创建
        tables_to_check = ['users', 'permission_requests',
                           'user_sessions', 'audit_logs']
        print("\n验证表创建:")
        for table in tables_to_check:
            if check_table_exists(cursor, table):
                print(f"✓ {table} 表创建成功")
            else:
                print(f"❌ {table} 表创建失败")

        # 检查视图
        cursor.execute("""
            SELECT viewname FROM pg_views 
            WHERE schemaname = 'public' 
            AND viewname IN ('user_permissions_view', 'permission_requests_view');
        """)
        views = cursor.fetchall()
        print(f"✓ 创建了 {len(views)} 个视图")

        # 检查默认管理员用户
        cursor.execute(
            "SELECT username, email, role FROM users WHERE role = 'admin';")
        admin_users = cursor.fetchall()
        print(f"✓ 创建了 {len(admin_users)} 个管理员用户")
        for admin in admin_users:
            print(f"  - {admin[0]} ({admin[1]})")

        print(f"\n🎉 用户管理系统迁移完成!")
        print(f"默认管理员登录信息:")
        print(f"  用户名: admin")
        print(f"  邮箱: admin@alex.com")
        print(f"  密码: admin123")
        print(f"  ⚠️  请在生产环境中修改默认密码!")

    except psycopg2.Error as e:
        print(f"❌ 数据库错误: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def create_test_data():
    """创建测试数据"""
    print("\n=== 创建测试数据 ===")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 创建测试用户
        test_users = [
            {
                'username': 'testuser1',
                'email': 'user1@test.com',
                'password': 'test123',
                'full_name': '测试用户1'
            },
            {
                'username': 'testuser2',
                'email': 'user2@test.com',
                'password': 'test123',
                'full_name': '测试用户2'
            }
        ]

        for user in test_users:
            password_hash = hash_password(user['password'])
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, status, role)
                VALUES (%s, %s, %s, %s, 'pending', 'user')
                ON CONFLICT (username) DO NOTHING;
            """, (user['username'], user['email'], password_hash, user['full_name']))

        # 创建测试权限申请
        cursor.execute("""
            INSERT INTO permission_requests (user_id, request_reason, requested_duration)
            SELECT id, '我需要使用系统进行学习匹配', '1month'
            FROM users WHERE username = 'testuser1';
        """)

        cursor.execute("""
            INSERT INTO permission_requests (user_id, request_reason, requested_duration)
            SELECT id, '希望能够访问系统查找合适的课程', '3months' 
            FROM users WHERE username = 'testuser2';
        """)

        conn.commit()
        print("✓ 测试数据创建成功")

        # 显示创建的数据
        cursor.execute(
            "SELECT username, email, status FROM users WHERE role = 'user';")
        users = cursor.fetchall()
        print(f"创建了 {len(users)} 个测试用户:")
        for user in users:
            print(f"  - {user[0]} ({user[1]}) - {user[2]}")

        cursor.execute("SELECT COUNT(*) FROM permission_requests;")
        req_count = cursor.fetchone()[0]
        print(f"创建了 {req_count} 个权限申请")

    except Exception as e:
        print(f"❌ 创建测试数据失败: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='用户管理系统数据库迁移')
    parser.add_argument('--test-data', action='store_true', help='创建测试数据')
    parser.add_argument('--check-config', action='store_true', help='检查数据库配置')

    args = parser.parse_args()

    if args.check_config:
        print("数据库配置:")
        for key, value in DB_CONFIG.items():
            if key == 'password':
                print(f"  {key}: {'*' * len(str(value))}")
            else:
                print(f"  {key}: {value}")
        sys.exit(0)

    # 执行迁移
    migrate_user_management()

    # 如果指定了创建测试数据
    if args.test_data:
        create_test_data()
