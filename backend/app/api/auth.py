from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from ..config import Settings, get_settings

router = APIRouter()
ph = PasswordHasher()

class LoginRequest(BaseModel):
    apiKey: str

@router.post("/auth/login")
async def login(request: LoginRequest, settings: Settings = Depends(get_settings)):
    if not settings.ADMIN_API_KEY_HASH:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin API key is not configured on the server.",
        )
    
    try:
        ph.verify(settings.ADMIN_API_KEY_HASH, request.apiKey)
        # The key is valid
        return {"message": "Authentication successful"}
    except VerifyMismatchError:
        # The key is invalid
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    except Exception:
        # Handle other potential errors during verification
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during authentication.",
        ) 