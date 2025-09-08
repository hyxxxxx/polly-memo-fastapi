"""
API密钥认证模块
"""
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader
from typing import Optional

from app.core.config import settings

# API密钥头部认证
api_key_header = APIKeyHeader(
    name="X-API-Key", 
    auto_error=False,
    description="API密钥，通过X-API-Key头部传递"
)

# Bearer token认证
bearer_auth = HTTPBearer(auto_error=False, description="Bearer token认证")


def validate_api_key(api_key: str) -> bool:
    """
    验证API密钥是否有效
    
    Args:
        api_key: 待验证的API密钥
        
    Returns:
        bool: 验证结果
    """
    if not api_key:
        return False
    
    # 检查主API密钥
    if settings.api_key and api_key == settings.api_key:
        return True
    
    # 检查多个API密钥
    if settings.api_keys and api_key in settings.api_keys:
        return True
    
    return False


async def get_api_key_from_header(api_key_header_value: Optional[str] = Security(api_key_header)) -> str:
    """
    从X-API-Key头部获取API密钥
    
    Args:
        api_key_header_value: X-API-Key头部值
        
    Returns:
        str: 验证过的API密钥
        
    Raises:
        HTTPException: 当API密钥无效或缺失时
    """
    if not settings.enable_api_key_auth:
        # 如果禁用了API密钥认证，直接通过
        return "disabled"
    
    if not api_key_header_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少API密钥，请在X-API-Key头部提供有效的API密钥",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if not validate_api_key(api_key_header_value):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API密钥",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key_header_value


async def get_api_key_from_bearer(credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_auth)) -> str:
    """
    从Authorization: Bearer头部获取API密钥
    
    Args:
        credentials: Bearer认证凭据
        
    Returns:
        str: 验证过的API密钥
        
    Raises:
        HTTPException: 当API密钥无效或缺失时
    """
    if not settings.enable_api_key_auth:
        # 如果禁用了API密钥认证，直接通过
        return "disabled"
    
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少Bearer token，请在Authorization头部提供有效的Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not validate_api_key(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials.credentials


async def require_api_key(
    header_key: Optional[str] = Security(api_key_header),
    bearer_token: Optional[HTTPAuthorizationCredentials] = Security(bearer_auth)
) -> str:
    """
    要求API密钥认证 - 支持两种方式：X-API-Key头部或Bearer token
    
    优先级：X-API-Key > Authorization: Bearer
    
    Args:
        header_key: X-API-Key头部值
        bearer_token: Bearer认证凭据
        
    Returns:
        str: 验证过的API密钥
        
    Raises:
        HTTPException: 当API密钥无效或缺失时
    """
    if not settings.enable_api_key_auth:
        # 如果禁用了API密钥认证，直接通过
        return "disabled"
    
    # 首先尝试X-API-Key头部
    if header_key and validate_api_key(header_key):
        return header_key
    
    # 然后尝试Bearer token
    if bearer_token and bearer_token.credentials and validate_api_key(bearer_token.credentials):
        return bearer_token.credentials
    
    # 都没有找到有效的API密钥
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="需要有效的API密钥。请通过X-API-Key头部或Authorization: Bearer头部提供API密钥",
        headers={"WWW-Authenticate": "ApiKey, Bearer"},
    )


# 导出常用的依赖
api_key_required = require_api_key 