"""
用户管理相关的API路由
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import List, Optional
import psycopg2
import secrets
import string

try:
    from .models import (
        UserRegister, UserLogin, UserUpdate, PermissionRequest, PermissionReview,
        PermissionUpdate, UserResponse, PermissionRequestResponse,
        LoginResponse, MessageResponse, AdminStats, PasswordResetRequest, PasswordReset,
        ChangePassword, PasswordChange
    )
    from .auth import (
        authenticate_user, create_user_session, logout_user, hash_password,
        get_current_user, get_current_active_user, get_current_admin_user,
        verify_password
    )
    from .database import (
        UserDatabase, PermissionRequestDatabase, AuditDatabase, StatsDatabase, PasswordResetDatabase,
        DatabaseError
    )
    from .email_service import email_service
except ImportError:
    from models import (
        UserRegister, UserLogin, UserUpdate, PermissionRequest, PermissionReview,
        PermissionUpdate, UserResponse, PermissionRequestResponse,
        LoginResponse, MessageResponse, AdminStats, PasswordResetRequest, PasswordReset,
        ChangePassword, PasswordChange
    )
    from auth import (
        authenticate_user, create_user_session, logout_user, hash_password,
        get_current_user, get_current_active_user, get_current_admin_user,
        verify_password
    )
    from database import (
        UserDatabase, PermissionRequestDatabase, AuditDatabase, StatsDatabase, PasswordResetDatabase,
        DatabaseError
    )
    from email_service import email_service

router = APIRouter(prefix="/api/users", tags=["用户管理"])


@router.post("/register", response_model=MessageResponse)
async def register_user(user_data: UserRegister, request: Request):
    """用户注册"""
    try:
        # 检查用户名是否已存在
        existing_user = UserDatabase.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

        # 检查邮箱是否已存在
        existing_email = UserDatabase.get_user_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )

        # 创建用户
        password_hash = hash_password(user_data.password)
        user_id = UserDatabase.create_user(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash,
            full_name=user_data.full_name
        )

        # 记录审计日志
        client_ip = request.client.host
        AuditDatabase.log_action(
            user_id=user_id,
            action="user_register",
            details={"username": user_data.username, "email": user_data.email},
            ip_address=client_ip
        )

        return MessageResponse(
            message="注册成功！请登录后申请访问权限。",
            success=True
        )

    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/login", response_model=LoginResponse)
async def login_user(user_data: UserLogin, request: Request):
    """用户登录"""
    try:
        # 验证用户身份
        user = await authenticate_user(user_data.username, user_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        # 检查用户状态
        if user['status'] == 'suspended':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被暂停，请联系管理员"
            )

        if user['status'] == 'inactive':
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,  # 使用423状态码表示账户被锁定
                detail="账户已被禁用，需要重新申请权限"
            )

        # 创建会话
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        access_token = await create_user_session(user, client_ip, user_agent)

        # 构造用户响应
        user_response = UserResponse(
            id=user['id'],
            username=user['username'],
            email=user['email'],
            full_name=user['full_name'],
            status=user['status'],
            role=user['role'],
            permission_granted_at=user['permission_granted_at'],
            permission_expires_at=user['permission_expires_at'],
            created_at=user['created_at'],
            last_login=user['last_login']
        )

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )

    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/logout", response_model=MessageResponse)
async def logout_user_endpoint(current_user: dict = Depends(get_current_user), request: Request = None):
    """用户登出"""
    try:
        # 从请求头获取token
        token = request.headers.get("authorization", "").replace("Bearer ", "")
        if token:
            await logout_user(token)

        # 记录审计日志
        client_ip = request.client.host if request else None
        AuditDatabase.log_action(
            user_id=current_user['id'],
            action="user_logout",
            ip_address=client_ip
        )

        return MessageResponse(message="登出成功", success=True)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出失败"
        )


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """获取用户个人信息"""
    return UserResponse(
        id=current_user['id'],
        username=current_user['username'],
        email=current_user['email'],
        full_name=current_user['full_name'],
        status=current_user['status'],
        role=current_user['role'],
        permission_granted_at=current_user['permission_granted_at'],
        permission_expires_at=current_user['permission_expires_at'],
        created_at=current_user['created_at'],
        last_login=current_user['last_login']
    )


@router.put("/profile", response_model=MessageResponse)
async def update_user_profile(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """更新用户个人信息"""
    try:
        update_data = {}

        if user_data.username is not None:
            # 检查用户名是否被其他用户使用
            existing_user = UserDatabase.get_user_by_username(
                user_data.username)
            if existing_user and existing_user['id'] != current_user['id']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已被其他用户使用"
                )
            update_data['username'] = user_data.username

        if user_data.full_name is not None:
            update_data['full_name'] = user_data.full_name

        if user_data.email is not None:
            # 检查邮箱是否被其他用户使用
            existing_user = UserDatabase.get_user_by_email(user_data.email)
            if existing_user and existing_user['id'] != current_user['id']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已被其他用户使用"
                )
            update_data['email'] = user_data.email

        if update_data:
            success = UserDatabase.update_user(
                current_user['id'], **update_data)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="更新失败"
                )

            # 记录审计日志
            client_ip = request.client.host if request else None
            AuditDatabase.log_action(
                user_id=current_user['id'],
                action="user_profile_update",
                details=update_data,
                ip_address=client_ip
            )

        return MessageResponse(message="个人信息更新成功", success=True)

    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """修改密码"""
    try:
        # 验证原密码
        if not verify_password(password_data.old_password, current_user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="原密码错误"
            )

        # 更新密码
        new_password_hash = hash_password(password_data.new_password)
        success = UserDatabase.update_user(
            current_user['id'],
            password_hash=new_password_hash
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密码修改失败"
            )

        # 记录审计日志
        client_ip = request.client.host if request else None
        AuditDatabase.log_action(
            user_id=current_user['id'],
            action="password_change",
            ip_address=client_ip
        )

        return MessageResponse(message="密码修改成功", success=True)

    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/request-permission", response_model=MessageResponse)
async def request_permission(
    request_data: PermissionRequest,
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """申请访问权限"""
    try:
        # 检查是否已有待处理的申请
        existing_requests = PermissionRequestDatabase.get_user_requests(
            current_user['id'])
        pending_requests = [
            req for req in existing_requests if req['status'] == 'pending']

        if pending_requests:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="您已有待处理的权限申请，请等待审批结果"
            )

        # 创建权限申请
        request_id = PermissionRequestDatabase.create_request(
            user_id=current_user['id'],
            request_reason=request_data.request_reason,
            requested_duration=request_data.requested_duration,
            additional_info=getattr(request_data, 'additional_info', None)
        )

        # 记录审计日志
        client_ip = request.client.host if request else None
        AuditDatabase.log_action(
            user_id=current_user['id'],
            action="permission_request_create",
            entity_type="permission_request",
            entity_id=request_id,
            details={
                "reason": request_data.request_reason,
                "duration": request_data.requested_duration
            },
            ip_address=client_ip
        )

        return MessageResponse(
            message="权限申请提交成功！请等待管理员审批。",
            success=True
        )

    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/my-requests", response_model=List[PermissionRequestResponse])
async def get_my_permission_requests(current_user: dict = Depends(get_current_user)):
    """获取我的权限申请"""
    try:
        requests = PermissionRequestDatabase.get_user_requests(
            current_user['id'])
        return [PermissionRequestResponse(**request) for request in requests]

    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/request-permission-extension", response_model=MessageResponse)
async def request_permission_extension(
    request_data: dict,
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """申请权限续期"""
    try:
        # 检查用户是否已有权限
        if current_user['status'] != 'active':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只有已激活的用户才能申请权限续期"
            )

        # 检查是否已有待处理的续期申请
        existing_requests = PermissionRequestDatabase.get_user_requests(
            current_user['id'])
        pending_extension_requests = [
            req for req in existing_requests
            if req['status'] == 'pending' and req['request_reason'] == '权限续期申请'
        ]

        if pending_extension_requests:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="您已有待处理的权限续期申请，请等待审批结果"
            )

        # 创建权限续期申请
        request_id = PermissionRequestDatabase.create_request(
            user_id=current_user['id'],
            request_reason='权限续期申请',
            requested_duration=request_data.get('requested_duration', '1'),
            additional_info=request_data.get('additional_info', '')
        )

        # 记录审计日志
        AuditDatabase.log_action(
            user_id=current_user['id'],
            action='request_permission_extension',
            details={
                'request_id': request_id,
                'reason': request_data.get('reason', ''),
                'requested_duration': request_data.get('requested_duration', '1'),
                'additional_info': request_data.get('additional_info', '')
            },
            ip_address=request.client.host if request else None
        )

        return MessageResponse(message="权限续期申请已提交，等待管理员审核")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# 管理员相关接口


@router.get("/admin/stats", response_model=AdminStats)
async def get_admin_stats(current_admin: dict = Depends(get_current_admin_user)):
    """获取管理员统计信息"""
    try:
        stats = StatsDatabase.get_admin_stats()
        return AdminStats(**stats)

    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/admin/users", response_model=List[UserResponse])
async def get_all_users(
    limit: int = 50,
    offset: int = 0,
    current_admin: dict = Depends(get_current_admin_user)
):
    """获取所有用户列表"""
    try:
        users = UserDatabase.get_all_users(limit=limit, offset=offset)
        return [UserResponse(**user) for user in users]

    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/admin/requests", response_model=List[PermissionRequestResponse])
async def get_all_permission_requests(
    pending_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    current_admin: dict = Depends(get_current_admin_user)
):
    """获取所有权限申请"""
    try:
        if pending_only:
            requests = PermissionRequestDatabase.get_pending_requests()
        else:
            requests = PermissionRequestDatabase.get_all_requests(
                limit=limit, offset=offset)

        return [PermissionRequestResponse(**request) for request in requests]

    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/admin/review-request", response_model=MessageResponse)
async def review_permission_request(
    review_data: PermissionReview,
    current_admin: dict = Depends(get_current_admin_user),
    request: Request = None
):
    """审批权限申请"""
    try:
        # 获取申请信息
        permission_request = PermissionRequestDatabase.get_request_by_id(
            review_data.request_id)
        if not permission_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="权限申请不存在"
            )

        if permission_request['status'] != 'pending':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该申请已被处理"
            )

        # 审批申请
        success = PermissionRequestDatabase.review_request(
            request_id=review_data.request_id,
            approved=review_data.approved,
            reviewed_by=current_admin['id'],
            reviewer_comments=review_data.reviewer_comments,
            approved_duration=review_data.approved_duration
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="审批操作失败"
            )

        # 如果批准，则授予用户权限
        if review_data.approved and review_data.approved_duration:
            UserDatabase.grant_permission(
                user_id=permission_request['user_id'],
                duration=review_data.approved_duration,
                granted_by=current_admin['id']
            )

        # 记录审计日志
        client_ip = request.client.host if request else None
        AuditDatabase.log_action(
            user_id=current_admin['id'],
            action="permission_request_review",
            entity_type="permission_request",
            entity_id=review_data.request_id,
            details={
                "approved": review_data.approved,
                "target_user_id": permission_request['user_id'],
                "approved_duration": review_data.approved_duration,
                "comments": review_data.reviewer_comments
            },
            ip_address=client_ip
        )

        result_msg = "权限申请已批准" if review_data.approved else "权限申请已拒绝"
        return MessageResponse(message=result_msg, success=True)

    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/admin/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    current_admin: dict = Depends(get_current_admin_user),
    request: Request = None
):
    """删除用户"""
    try:
        # 不能删除管理员用户
        user = UserDatabase.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        if user['role'] == 'admin':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除管理员用户"
            )

        # 删除用户
        success = UserDatabase.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除用户失败"
            )

        # 记录审计日志
        client_ip = request.client.host if request else None
        AuditDatabase.log_action(
            user_id=current_admin['id'],
            action="user_delete",
            entity_type="user",
            entity_id=user_id,
            details={"deleted_username": user['username']},
            ip_address=client_ip
        )

        return MessageResponse(message="用户删除成功", success=True)

    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/admin/requests/{request_id}", response_model=MessageResponse)
async def delete_permission_request(
    request_id: int,
    current_admin: dict = Depends(get_current_admin_user),
    request: Request = None
):
    """删除权限申请"""
    try:
        # 检查申请是否存在
        permission_request = PermissionRequestDatabase.get_request_by_id(
            request_id)
        if not permission_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="权限申请不存在"
            )

        # 删除申请
        success = PermissionRequestDatabase.delete_request(request_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除权限申请失败"
            )

        # 记录审计日志
        client_ip = request.client.host if request else None
        AuditDatabase.log_action(
            user_id=current_admin['id'],
            action="permission_request_delete",
            entity_type="permission_request",
            entity_id=request_id,
            details={
                "deleted_user_id": permission_request['user_id'],
                "request_status": permission_request['status']
            },
            ip_address=client_ip
        )

        return MessageResponse(message="权限申请删除成功", success=True)

    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/admin/users/{user_id}/permission", response_model=MessageResponse)
async def update_user_permission(
    user_id: int,
    permission_data: PermissionUpdate,
    current_admin: dict = Depends(get_current_admin_user),
    request: Request = None
):
    """更新用户权限时长"""
    try:
        # 检查用户是否存在
        user = UserDatabase.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        if user['role'] == 'admin':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能修改管理员权限"
            )

        # 更新用户权限
        success = UserDatabase.update_user_permission(
            user_id=user_id,
            days=permission_data.days,
            granted_by=current_admin['id']
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新权限失败"
            )

        # 记录审计日志
        client_ip = request.client.host if request else None
        AuditDatabase.log_action(
            user_id=current_admin['id'],
            action="permission_update",
            entity_type="user",
            entity_id=user_id,
            details={
                "updated_username": user['username'],
                "permission_days": permission_data.days,
                "permission_type": "永久" if permission_data.days == -1 else f"{permission_data.days}天"
            },
            ip_address=client_ip
        )

        if permission_data.days == -1:
            permission_type = "永久权限"
        elif permission_data.days == 0:
            permission_type = "立即过期（已禁用）"
        else:
            permission_type = f"{permission_data.days}天权限"
        return MessageResponse(message=f"权限更新成功，设置为{permission_type}", success=True)

    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/admin/users/{user_id}/status", response_model=MessageResponse)
async def update_user_status(
    user_id: int,
    user_data: UserUpdate,
    current_admin: dict = Depends(get_current_admin_user),
    request: Request = None
):
    """更新用户状态"""
    try:
        user = UserDatabase.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        if user['role'] == 'admin':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能修改管理员用户状态"
            )

        update_data = {}
        if user_data.status is not None:
            update_data['status'] = user_data.status

        if update_data:
            success = UserDatabase.update_user(user_id, **update_data)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="状态更新失败"
                )

        # 记录审计日志
        client_ip = request.client.host if request else None
        AuditDatabase.log_action(
            user_id=current_admin['id'],
            action="user_status_update",
            entity_type="user",
            entity_id=user_id,
            details={"new_status": user_data.status,
                     "target_username": user['username']},
            ip_address=client_ip
        )

        return MessageResponse(message="用户状态更新成功", success=True)

    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# 密码重置相关API
@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    reset_request: PasswordResetRequest,
    request: Request = None
):
    """发送密码重置邮件"""
    try:
        # 验证邮箱格式
        email = reset_request.email.lower().strip()

        # 查找用户
        user = UserDatabase.get_user_by_email(email)
        if not user:
            # 为了安全，即使用户不存在也返回成功消息
            return MessageResponse(
                message="如果该邮箱已注册，您将收到密码重置邮件",
                success=True
            )

        # 生成安全的重置token
        token = ''.join(secrets.choice(string.ascii_letters +
                        string.digits) for _ in range(64))

        # 获取客户端IP
        client_ip = request.client.host if request else None

        # 保存重置token到数据库
        token_id = PasswordResetDatabase.create_reset_token(
            user_id=user['id'],
            token=token,
            ip_address=client_ip
        )

        if not token_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建重置token失败"
            )

        # 发送重置邮件
        email_sent = email_service.send_password_reset_email(
            to_email=email,
            reset_token=token,
            username=user['username']
        )

        if not email_sent:
            # 删除创建的token
            PasswordResetDatabase.mark_token_used(token)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="发送邮件失败，请稍后重试"
            )

        # 记录审计日志
        AuditDatabase.log_action(
            user_id=user['id'],
            action="password_reset_request",
            entity_type="user",
            entity_id=user['id'],
            details={"email": email},
            ip_address=client_ip
        )

        return MessageResponse(
            message="如果该邮箱已注册，您将收到密码重置邮件",
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="处理密码重置请求失败"
        )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    reset_data: PasswordReset,
    request: Request = None
):
    """执行密码重置"""
    try:
        # 验证重置token
        token_info = PasswordResetDatabase.verify_reset_token(reset_data.token)
        if not token_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="重置链接无效或已过期"
            )

        # 获取用户信息
        user = UserDatabase.get_user_by_id(token_info['user_id'])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 更新密码
        new_password_hash = hash_password(reset_data.new_password)
        success = UserDatabase.update_password(user['id'], new_password_hash)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密码更新失败"
            )

        # 标记token为已使用
        PasswordResetDatabase.mark_token_used(reset_data.token)

        # 记录审计日志
        client_ip = request.client.host if request else None
        AuditDatabase.log_action(
            user_id=user['id'],
            action="password_reset_completed",
            entity_type="user",
            entity_id=user['id'],
            details={"username": user['username']},
            ip_address=client_ip
        )

        return MessageResponse(
            message="密码重置成功，请使用新密码登录",
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码重置失败"
        )


@router.get("/verify-reset-token/{token}")
async def verify_reset_token(token: str):
    """验证重置token是否有效"""
    try:
        token_info = PasswordResetDatabase.verify_reset_token(token)
        if not token_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="重置链接无效或已过期"
            )

        return {
            "valid": True,
            "username": token_info['username'],
            "email": token_info['email']
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证token失败"
        )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    change_data: ChangePassword,
    current_user: dict = Depends(get_current_active_user),
    request: Request = None
):
    """已登录用户修改密码"""
    try:
        # 验证当前密码
        if not verify_password(change_data.current_password, current_user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前密码错误"
            )

        # 生成新密码哈希
        new_password_hash = hash_password(change_data.new_password)

        # 更新密码
        success = UserDatabase.update_password(
            current_user['id'], new_password_hash)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密码更新失败"
            )

        # 记录审计日志
        client_ip = request.client.host if request else None
        AuditDatabase.log_action(
            user_id=current_user['id'],
            action="password_changed",
            entity_type="user",
            entity_id=current_user['id'],
            details={"username": current_user['username']},
            ip_address=client_ip
        )

        return MessageResponse(
            message="密码修改成功",
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改密码失败"
        )
