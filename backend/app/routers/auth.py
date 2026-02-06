from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.database import User, UserGamification, get_db
import os
import random
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "finsakhi-secret-key-2024")
ALGORITHM = "HS256"

# Twilio Verify Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_VERIFY_SERVICE_SID = os.getenv("TWILIO_VERIFY_SERVICE_SID")

# Debug logging
print(f"🔧 Twilio Config:")
print(f"   Account SID: {TWILIO_ACCOUNT_SID[:10]}..." if TWILIO_ACCOUNT_SID else "   Account SID: Not set")
print(f"   Auth Token: {'Set' if TWILIO_AUTH_TOKEN else 'Not set'}")
print(f"   Service SID: {TWILIO_VERIFY_SERVICE_SID[:10]}..." if TWILIO_VERIFY_SERVICE_SID else "   Service SID: Not set")

# Initialize Twilio client
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        print(f"✅ Twilio client initialized successfully")
    except Exception as e:
        print(f"❌ Twilio client initialization failed: {e}")
else:
    print(f"⚠️  Twilio client not initialized - missing credentials")

# Pydantic models
class SendOTPRequest(BaseModel):
    phone: str
    language: str = "en"

class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str
    name: str = None  # Optional, can be provided later

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def generate_otp():
    """Generate 6-digit OTP"""
    return str(random.randint(100000, 999999))

@router.post("/send-otp")
def send_otp(data: SendOTPRequest, db: Session = Depends(get_db)):
    """Send OTP to Aadhaar-linked mobile number via Twilio Verify"""
    
    # Check if user exists, create placeholder if not
    user = db.query(User).filter(User.phone == data.phone).first()
    
    if not user:
        # New user - create placeholder
        user = User(
            phone=data.phone,
            language=data.language
        )
        db.add(user)
    else:
        # Update language preference
        user.language = data.language
    
    db.commit()
    
    # Send OTP via Twilio Verify API
    if twilio_client and TWILIO_VERIFY_SERVICE_SID:
        try:
            verification = twilio_client.verify \
                .v2 \
                .services(TWILIO_VERIFY_SERVICE_SID) \
                .verifications \
                .create(to=data.phone, channel='sms')
            
            return {
                "success": True,
                "message": "OTP sent successfully to your mobile via SMS",
                "phone": data.phone,
                "status": verification.status,
                "valid_for": "10 minutes"
            }
        except Exception as e:
            # Log the error and return demo mode response
            print(f"Twilio Error: {str(e)}")
            # Fall through to demo mode below
    else:
        # Demo mode - generate and store OTP locally
        otp = generate_otp()
        otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        
        user.otp = otp
        user.otp_expiry = otp_expiry
        db.commit()
        
        return {
            "success": True,
            "message": "OTP generated (Demo mode - Twilio not configured)",
            "phone": data.phone,
            "otp": otp,  # Only shown in demo mode
            "note": "In production, OTP will be sent via SMS"
        }

@router.post("/verify-otp")
def verify_otp(data: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Verify OTP and login/signup user"""
    
    # Find user
    user = db.query(User).filter(User.phone == data.phone).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Phone number not found. Please request OTP first.")
    
    # Verify OTP via Twilio Verify API
    if twilio_client and TWILIO_VERIFY_SERVICE_SID:
        try:
            verification_check = twilio_client.verify \
                .v2 \
                .services(TWILIO_VERIFY_SERVICE_SID) \
                .verification_checks \
                .create(to=data.phone, code=data.otp)
            
            if verification_check.status != 'approved':
                raise HTTPException(status_code=401, detail="Invalid or expired OTP")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"OTP verification failed: {str(e)}")
    else:
        # Demo mode - check local OTP
        if not user.otp or user.otp != data.otp:
            raise HTTPException(status_code=401, detail="Invalid OTP")
        
        if user.otp_expiry and user.otp_expiry < datetime.utcnow():
            raise HTTPException(status_code=401, detail="OTP expired. Please request a new one.")
        
        # Clear OTP after successful verification
        user.otp = None
        user.otp_expiry = None
    
    # Update user name if provided
    if data.name:
        user.name = data.name
    
    # Check if gamification record exists
    gamification = db.query(UserGamification).filter(
        UserGamification.user_id == user.id
    ).first()
    
    if not gamification:
        # New user - create gamification record
        gamification = UserGamification(
            user_id=user.id,
            total_xp=0,
            current_level=1
        )
        db.add(gamification)
    
    db.commit()
    db.refresh(user)
    
    # Create token
    token = create_access_token({"user_id": user.id})
    
    return {
        "token": token,
        "user_id": user.id,
        "name": user.name or "User",
        "language": user.language,
        "total_xp": gamification.total_xp,
        "level": gamification.current_level,
        "message": "Login successful!"
    }

@router.get("/me")
def get_profile(user_id: int, db: Session = Depends(get_db)):
    """Get current user profile"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    gamification = db.query(UserGamification).filter(
        UserGamification.user_id == user_id
    ).first()
    
    return {
        "id": user.id,
        "name": user.name,
        "phone": user.phone,
        "email": user.email,
        "language": user.language,
        "total_xp": gamification.total_xp if gamification else 0,
        "level": gamification.current_level if gamification else 1
    }