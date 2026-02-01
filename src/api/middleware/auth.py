"""
Middleware de autenticação
"""
from fastapi import HTTPException, status, Header
from typing import Optional

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def require_api_key(authorization: Optional[str] = Header(None)) -> str:
    """
    Dependency para validar API key
    
    Usage:
        @app.get("/protected")
        async def protected_route(api_key: str = Depends(require_api_key)):
            ...
    
    Args:
        authorization: Header Authorization com formato "Bearer {api_key}"
        
    Returns:
        API key validada
        
    Raises:
        HTTPException 401/403 se não autorizado
    """
    if not authorization:
        logger.warning("Tentativa de acesso sem API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key não fornecida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extrair API key do header
    try:
        scheme, api_key = authorization.split()
        
        if scheme.lower() != "bearer":
            raise ValueError("Scheme inválido")
            
    except (ValueError, AttributeError):
        logger.warning("Formato de autorização inválido", header=authorization)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de autorização inválido. Use: Bearer {api_key}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validar API key
    if api_key != settings.API_KEY:
        logger.warning("API key inválida", provided_key=api_key[:8] + "...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key inválida",
        )
    
    return api_key


def optional_api_key(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    Dependency para API key opcional
    Retorna None se não fornecida, valida se fornecida
    
    Args:
        authorization: Header Authorization
        
    Returns:
        API key ou None
    """
    if not authorization:
        return None
    
    try:
        return require_api_key(authorization)
    except HTTPException:
        return None