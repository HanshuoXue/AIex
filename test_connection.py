#!/usr/bin/env python3
"""
测试PostgreSQL连接
### 重置用户密码
```bash
# 重置单个用户密码
python reset_user_password.py <username> <new_password>

# 示例
python reset_user_password.py admin admin123
python reset_user_password.py testuser test123
```

### 查看所有用户
```bash
python reset_user_password.py list
```

### 快速创建测试用户
```bash
# 注册新用户
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser1", 
    "email": "test1@example.com",
    "password": "test123",
    "confirm_password": "test123"
  }'
"""
import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import psycopg2
    from dotenv import load_dotenv

    # 加载环境变量
    load_dotenv()

    def test_connection():
        """测试数据库连接"""
        try:
            # 从环境变量获取配置
            db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME', 'Alex'),
                'user': os.getenv('DB_USER', 'xuehanshuo'),
                'password': os.getenv('DB_PASSWORD', 'xuehanshuo')
            }

            print("🔍 尝试连接数据库...")
            print(
                f"配置: {db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")

            # 连接数据库
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()

            # 测试查询
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ 连接成功! PostgreSQL版本: {version[0]}")

            # 检查当前用户和数据库
            cursor.execute("SELECT current_user, current_database();")
            user, db = cursor.fetchone()
            print(f"👤 当前用户: {user}")
            print(f"🗄️  当前数据库: {db}")

            # 检查programs表是否存在
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'programs'
                );
            """)
            table_exists = cursor.fetchone()[0]

            if table_exists:
                print("✅ programs表已存在")
                cursor.execute("SELECT COUNT(*) FROM programs;")
                count = cursor.fetchone()[0]
                print(f"📊 programs表中有 {count} 条记录")
            else:
                print("⚠️  programs表不存在，需要运行建表脚本")
                print("💡 请在pgAdmin4中运行 scripts/postgre/postgre.sql")

            cursor.close()
            conn.close()
            print("🎉 数据库连接测试完成!")

        except psycopg2.Error as e:
            print(f"❌ 数据库连接失败: {e}")
            print("\n🔧 请检查:")
            print("1. PostgreSQL服务是否运行")
            print("2. 数据库配置是否正确")
            print("3. 用户密码是否正确")
            print("4. 在pgAdmin4中重置xuehanshuo用户密码")
        except Exception as e:
            print(f"❌ 其他错误: {e}")

    if __name__ == "__main__":
        test_connection()

except ImportError as e:
    print(f"❌ 缺少依赖: {e}")
    print("💡 请先安装: pip install psycopg2-binary python-dotenv")
