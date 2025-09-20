"""
用户认证和授权模块
"""
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import hashlib

try:
    from .models import UserRole
    from .database import UserDatabase, SessionDatabase, AuditDatabase
except ImportError:
    from models import UserRole
    from database import UserDatabase, SessionDatabase, AuditDatabase

# JWT配置
SECRET_KEY = os.getenv(
    'JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# HTTP Bearer scheme
security = HTTPBearer()


class AuthenticationError(Exception):
    """认证错误异常"""
    pass


class AuthorizationError(Exception):
    """授权错误异常"""
    pass


def hash_password(password: str) -> str:
    """生成密码hash"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """验证JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token已过期")
    except jwt.JWTError:
        raise AuthenticationError("无效的token")


def hash_token(token: str) -> str:
    """对token进行hash处理用于数据库存储"""
    return hashlib.sha256(token.encode()).hexdigest()


async def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """验证用户身份"""
    user = UserDatabase.get_user_by_username(username)
    if not user:
        return None

    if not verify_password(password, user['password_hash']):
        return None

    return user


async def create_user_session(user: Dict[str, Any], ip_address: str = None, user_agent: str = None) -> str:
    """创建用户会话"""
    # 创建JWT token
    token_data = {
        "user_id": user['id'],
        "username": user['username'],
        "role": user['role']
    }

    access_token = create_access_token(token_data)
    token_hash = hash_token(access_token)

    # 计算过期时间
    expires_at = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    # 存储会话信息
    SessionDatabase.create_session(
        user_id=user['id'],
        token_hash=token_hash,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent
    )

    # 更新用户最后登录时间
    UserDatabase.update_user_login_time(user['id'])

    # 记录审计日志
    AuditDatabase.log_action(
        user_id=user['id'],
        action="user_login",
        ip_address=ip_address
    )

    return access_token


async def logout_user(token: str):
    """用户登出"""
    token_hash = hash_token(token)
    SessionDatabase.delete_session(token_hash)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """获取当前用户信息"""
    try:
        token = credentials.credentials

        # 验证JWT token
        payload = verify_token(token)
        user_id = payload.get("user_id")

        if not user_id:
            raise AuthenticationError("无效的token")

        # 验证会话是否存在且有效
        token_hash = hash_token(token)
        session = SessionDatabase.validate_session(token_hash)

        if not session:
            raise AuthenticationError("会话已过期或无效")

        # 检查用户状态
        user = UserDatabase.get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("用户不存在")

        if user['status'] not in ['active', 'pending']:
            raise AuthenticationError("用户账户已被禁用")

        return user

    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证错误",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """获取当前活跃用户（需要有有效权限）"""
    # 检查用户是否有访问权限
    if current_user['role'] == UserRole.ADMIN:
        return current_user

    # 普通用户需要检查权限
    if current_user['status'] != 'active':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您的账户权限申请还未被批准，请耐心等待"
        )

    # 检查权限是否过期
    if current_user['permission_expires_at'] and current_user['permission_expires_at'] <= datetime.now():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您的访问权限已过期，请重新申请"
        )

    return current_user


async def get_current_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """获取当前管理员用户"""
    if current_user['role'] != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    return current_user


def check_permission_expiry():
    """检查并更新过期权限"""
    # 这个函数可以定期调用来清理过期权限
    # 可以通过定时任务来执行
    pass
