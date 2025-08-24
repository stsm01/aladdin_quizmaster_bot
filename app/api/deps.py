"""FastAPI dependencies"""

from fastapi import Header, HTTPException, status, Depends
from typing import Annotated

from ..core.config import settings

def verify_admin_key(x_api_key: Annotated[str, Header(alias="X-API-Key")]) -> str:
    """Verify admin API key"""
    if x_api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return x_api_key

# Dependency for admin authentication
AdminAuth = Depends(verify_admin_key)
