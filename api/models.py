"""
用户管理系统数据模型
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class UserStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class PermissionRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Duration(str, Enum):
    ONE_WEEK = "1week"
    ONE_MONTH = "1month"
    THREE_MONTHS = "3months"
    SIX_MONTHS = "6months"
    ONE_YEAR = "1year"
    # 支持自定义天数格式
    CUSTOM_DAYS = "custom_days"

# 用户注册模型


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('用户名至少需要3个字符')
        if len(v) > 50:
            raise ValueError('用户名不能超过50个字符')
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码至少需要6个字符')
        return v

# 用户登录模型


class UserLogin(BaseModel):
    username: str
    password: str

# 权限申请模型


class PermissionRequest(BaseModel):
    request_reason: Optional[str] = ""
    requested_duration: Duration

    @validator('request_reason')
    def validate_reason(cls, v):
        if v and len(v.strip()) < 10:
            raise ValueError('申请理由至少需要10个字符')
        return v.strip() if v else ""

# 权限申请审批模型


class PermissionReview(BaseModel):
    request_id: int
    approved: bool
    reviewer_comments: Optional[str] = None
    approved_duration: Optional[str] = None  # 改为str以支持自定义格式

    @validator('approved_duration')
    def validate_approved_duration(cls, v, values):
        if values.get('approved') and not v:
            raise ValueError('批准申请时必须指定权限时长')

        if v:
            # 检查是否为有效的预设值或自定义天数格式
            valid_presets = ['1week', '1month', '3months', '6months', '1year']
            if v not in valid_presets:
                # 检查是否为自定义天数格式 (数字+days)
                import re
                if not re.match(r'^\d+days?$', v):
                    raise ValueError('权限时长必须是预设值或自定义天数格式（如30days）')
        return v

# 用户信息更新模型


class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[UserStatus] = None

    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if len(v) < 3:
                raise ValueError('用户名至少需要3个字符')
            if len(v) > 50:
                raise ValueError('用户名不能超过50个字符')
            import re
            if not re.match(r'^[a-zA-Z0-9_]+$', v):
                raise ValueError('用户名只能包含字母、数字和下划线')
        return v

# 权限修改模型


class PermissionUpdate(BaseModel):
    days: int  # -1表示永久权限，0表示立即过期，其他正数表示天数

    @validator('days')
    def validate_days(cls, v):
        if v < -1:
            raise ValueError('天数必须为-1（永久）、0（立即过期）或正整数')
        return v

# 密码修改模型


class PasswordChange(BaseModel):
    old_password: str
    new_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('新密码至少需要6个字符')
        return v

# 响应模型


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    status: UserStatus
    role: UserRole
    permission_granted_at: Optional[datetime]
    permission_expires_at: Optional[datetime]
    created_at: datetime
    last_login: Optional[datetime]


class PermissionRequestResponse(BaseModel):
    id: int
    user_id: int
    username: str
    email: str
    full_name: Optional[str]
    request_reason: str
    requested_duration: Duration
    additional_info: Optional[str]
    status: PermissionRequestStatus
    reviewed_by: Optional[int]
    reviewed_by_username: Optional[str]
    reviewed_at: Optional[datetime]
    reviewer_comments: Optional[str]
    approved_duration: Optional[str]  # 改为str以支持自定义天数格式
    created_at: datetime
    updated_at: datetime


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class MessageResponse(BaseModel):
    message: str
    success: bool = True

# 管理员统计信息


class AdminStats(BaseModel):
    total_users: int
    admin_users: int
    pending_requests: int
    active_users: int
    expired_permissions: int

# 密码重置相关模型


class PasswordResetRequest(BaseModel):
    email: str


class PasswordReset(BaseModel):
    token: str
    new_password: str
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('密码不匹配')
        return v

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6个字符')
        return v


class ChangePassword(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('新密码与确认密码不匹配')
        return v

    @validator('new_password')
    def validate_new_password(cls, v, values):
        if len(v) < 6:
            raise ValueError('密码长度至少6个字符')
        if 'current_password' in values and v == values['current_password']:
            raise ValueError('新密码不能与当前密码相同')
        return v
