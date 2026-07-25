"""Authentication endpoints with OTP using Redis."""

from fastapi import APIRouter, HTTPException, Request
from app.schemas import OTPRequest, OTPVerify, LoginResponse, MessageResponse
from app.services import AuthService
from app.utils import check_rate_limit, get_client_ip

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/otp", response_model=MessageResponse)
async def request_otp(
    request: Request,
    otp_request: OTPRequest
):
    """
    Request OTP for phone number.
    
    OTP is stored in Redis with 5-minute TTL.
    Rate limiting applied to prevent abuse.
    
    - **phone**: Phone number in E.164 format (e.g., +1234567890)
    """
    # Apply rate limiting
    client_ip = get_client_ip(request)
    await check_rate_limit(f"otp:{client_ip}")
    
    # Generate and store OTP
    otp = await AuthService.generate_otp(otp_request.phone)
    
    # In production, send OTP via SMS
    # For demo purposes, we'll return it in the response
    return MessageResponse(
        message=f"OTP sent to {otp_request.phone}. Demo OTP: {otp}"
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: OTPVerify
):
    """
    Login with OTP verification.
    
    Verifies OTP and deletes it from Redis after successful verification.
    
    - **phone**: Phone number
    - **otp**: 6-digit OTP code
    """
    # Apply rate limiting
    client_ip = get_client_ip(request)
    await check_rate_limit(f"login:{client_ip}")
    
    # Verify OTP
    is_valid = await AuthService.verify_otp(login_data.phone, login_data.otp)
    
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")
    
    # In production, create session and return token
    # For demo purposes, return mock user data
    user_id = abs(hash(login_data.phone)) % 10000
    
    return LoginResponse(
        user_id=user_id,
        phone=login_data.phone,
        message="Login successful"
    )
