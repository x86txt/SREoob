from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import hashlib
from ..config import Settings, get_settings

router = APIRouter()

class LoginRequest(BaseModel):
    apiKey: str

def verify_api_key(provided_key: str, stored_hash: str) -> bool:
    """Verify API key using SHA-256 hash comparison"""
    # Generate SHA-256 hash of the provided key
    provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
    
    # Compare with stored hash (support both plain keys and hashed keys for backward compatibility)
    if len(stored_hash) == 64 and all(c in '0123456789abcdef' for c in stored_hash.lower()):
        # Stored hash appears to be a hex hash, compare hashes
        return provided_hash == stored_hash.lower()
    else:
        # Stored value is plain text, compare directly (fallback for plain keys)
        return provided_key == stored_hash

@router.post("/auth/login")
async def login(request: LoginRequest, settings: Settings = Depends(get_settings)):
    if not settings.ADMIN_API_KEY_HASH:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin API key is not configured on the server.",
        )
    
    try:
        if verify_api_key(request.apiKey, settings.ADMIN_API_KEY_HASH):
            # The key is valid
            return {"message": "Authentication successful"}
        else:
            # The key is invalid
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key",
            )
    except Exception as e:
        # Handle other potential errors during verification
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during authentication.",
        ) 