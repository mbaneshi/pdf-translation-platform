# Authentication Service
# backend/app/services/auth_service.py

import re
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import logging

from app.models.user_models import User, UserSession, UserActivity
from app.core.config import settings

logger = logging.getLogger(__name__)

class AuthService:
    """Service for handling user authentication and authorization"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password_strength(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            return False
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            return False
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            return False
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            return False
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False
        
        return True
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_reset_token(self, email: str) -> str:
        """Create password reset token"""
        data = {"email": email, "type": "reset"}
        expire = datetime.utcnow() + timedelta(hours=1)  # Reset token expires in 1 hour
        data.update({"exp": expire})
        encoded_jwt = jwt.encode(data, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.error(f"Token verification failed: {e}")
            raise e
    
    def register_user(self, email: str, password: str, full_name: str, db: Session) -> Dict[str, Any]:
        """Register a new user"""
        try:
            # Validate email format
            if not self.validate_email(email):
                return {
                    "success": False,
                    "error": "Invalid email format"
                }
            
            # Validate password strength
            if not self.validate_password_strength(password):
                return {
                    "success": False,
                    "error": "Password must be at least 8 characters long and contain uppercase, lowercase, digit, and special character"
                }
            
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                return {
                    "success": False,
                    "error": "Email already exists"
                }
            
            # Create new user
            hashed_password = self.hash_password(password)
            verification_token = secrets.token_urlsafe(32)
            
            new_user = User(
                email=email,
                hashed_password=hashed_password,
                full_name=full_name,
                verification_token=verification_token,
                verification_token_expires=datetime.utcnow() + timedelta(hours=24),
                is_active=True,
                is_verified=False
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            # Log user activity
            self._log_user_activity(
                user_id=new_user.id,
                activity_type="registration",
                activity_description="User registered successfully",
                db=db
            )
            
            # TODO: Send verification email
            # send_verification_email(email, verification_token)
            
            return {
                "success": True,
                "user": {
                    "id": new_user.id,
                    "uuid": new_user.uuid,
                    "email": new_user.email,
                    "full_name": new_user.full_name,
                    "is_active": new_user.is_active,
                    "is_verified": new_user.is_verified,
                    "created_at": new_user.created_at
                },
                "message": "User registered successfully. Please check your email for verification."
            }
            
        except Exception as e:
            logger.error(f"User registration failed: {e}")
            db.rollback()
            return {
                "success": False,
                "error": "Registration failed. Please try again."
            }
    
    def authenticate_user(self, email: str, password: str, db: Session) -> Dict[str, Any]:
        """Authenticate user with email and password"""
        try:
            # Find user by email
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                return {
                    "success": False,
                    "error": "Invalid credentials"
                }
            
            # Check if user is active
            if not user.is_active:
                return {
                    "success": False,
                    "error": "Account is inactive. Please contact support."
                }
            
            # Verify password
            if not self.verify_password(password, user.hashed_password):
                return {
                    "success": False,
                    "error": "Invalid credentials"
                }
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()
            
            # Create tokens
            access_token_data = {
                "user_id": user.id,
                "email": user.email,
                "uuid": user.uuid
            }
            refresh_token_data = {
                "user_id": user.id,
                "email": user.email,
                "uuid": user.uuid
            }
            
            access_token = self.create_access_token(access_token_data)
            refresh_token = self.create_refresh_token(refresh_token_data)
            
            # Create session
            session = UserSession(
                user_id=user.id,
                session_token=access_token,
                refresh_token=refresh_token,
                expires_at=datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            )
            db.add(session)
            db.commit()
            
            # Log user activity
            self._log_user_activity(
                user_id=user.id,
                activity_type="login",
                activity_description="User logged in successfully",
                db=db
            )
            
            return {
                "success": True,
                "user": {
                    "id": user.id,
                    "uuid": user.uuid,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "last_login": user.last_login
                },
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60
            }
            
        except Exception as e:
            logger.error(f"User authentication failed: {e}")
            return {
                "success": False,
                "error": "Authentication failed. Please try again."
            }
    
    def logout_user(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Logout user and invalidate session"""
        try:
            # Deactivate all user sessions
            sessions = db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            ).all()
            
            for session in sessions:
                session.is_active = False
            
            db.commit()
            
            # Log user activity
            self._log_user_activity(
                user_id=user_id,
                activity_type="logout",
                activity_description="User logged out successfully",
                db=db
            )
            
            return {
                "success": True,
                "message": "Logged out successfully"
            }
            
        except Exception as e:
            logger.error(f"User logout failed: {e}")
            return {
                "success": False,
                "error": "Logout failed. Please try again."
            }
    
    def get_current_user(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get current user information"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return {
                    "success": False,
                    "error": "User not found"
                }
            
            return {
                "success": True,
                "user": {
                    "id": user.id,
                    "uuid": user.uuid,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "language_preference": user.language_preference,
                    "timezone": user.timezone,
                    "created_at": user.created_at,
                    "last_login": user.last_login
                }
            }
            
        except Exception as e:
            logger.error(f"Get current user failed: {e}")
            return {
                "success": False,
                "error": "Failed to get user information"
            }
    
    def request_password_reset(self, email: str, db: Session) -> Dict[str, Any]:
        """Request password reset"""
        try:
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                return {
                    "success": False,
                    "error": "User not found"
                }
            
            # Create reset token
            reset_token = self.create_reset_token(email)
            user.reset_token = reset_token
            user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
            
            db.commit()
            
            # Log user activity
            self._log_user_activity(
                user_id=user.id,
                activity_type="password_reset_request",
                activity_description="Password reset requested",
                db=db
            )
            
            # TODO: Send reset email
            # send_reset_email(email, reset_token)
            
            return {
                "success": True,
                "message": "Password reset email sent successfully"
            }
            
        except Exception as e:
            logger.error(f"Password reset request failed: {e}")
            return {
                "success": False,
                "error": "Password reset request failed. Please try again."
            }
    
    def confirm_password_reset(self, token: str, new_password: str, db: Session) -> Dict[str, Any]:
        """Confirm password reset with token"""
        try:
            # Verify token
            payload = self.verify_token(token)
            
            if payload.get("type") != "reset":
                return {
                    "success": False,
                    "error": "Invalid token type"
                }
            
            email = payload.get("email")
            if not email:
                return {
                    "success": False,
                    "error": "Invalid token"
                }
            
            # Find user
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return {
                    "success": False,
                    "error": "User not found"
                }
            
            # Validate new password
            if not self.validate_password_strength(new_password):
                return {
                    "success": False,
                    "error": "Password must be at least 8 characters long and contain uppercase, lowercase, digit, and special character"
                }
            
            # Update password
            user.hashed_password = self.hash_password(new_password)
            user.reset_token = None
            user.reset_token_expires = None
            
            db.commit()
            
            # Log user activity
            self._log_user_activity(
                user_id=user.id,
                activity_type="password_reset_confirm",
                activity_description="Password reset completed",
                db=db
            )
            
            return {
                "success": True,
                "message": "Password updated successfully"
            }
            
        except JWTError:
            return {
                "success": False,
                "error": "Invalid or expired token"
            }
        except Exception as e:
            logger.error(f"Password reset confirmation failed: {e}")
            return {
                "success": False,
                "error": "Password reset failed. Please try again."
            }
    
    def verify_user_email(self, token: str, db: Session) -> Dict[str, Any]:
        """Verify user email with token"""
        try:
            user = db.query(User).filter(User.verification_token == token).first()
            
            if not user:
                return {
                    "success": False,
                    "error": "Invalid verification token"
                }
            
            if user.verification_token_expires < datetime.utcnow():
                return {
                    "success": False,
                    "error": "Verification token expired"
                }
            
            # Mark user as verified
            user.is_verified = True
            user.verification_token = None
            user.verification_token_expires = None
            
            db.commit()
            
            # Log user activity
            self._log_user_activity(
                user_id=user.id,
                activity_type="email_verification",
                activity_description="Email verified successfully",
                db=db
            )
            
            return {
                "success": True,
                "message": "Email verified successfully"
            }
            
        except Exception as e:
            logger.error(f"Email verification failed: {e}")
            return {
                "success": False,
                "error": "Email verification failed. Please try again."
            }
    
    def _log_user_activity(self, user_id: int, activity_type: str, activity_description: str, db: Session):
        """Log user activity"""
        try:
            activity = UserActivity(
                user_id=user_id,
                activity_type=activity_type,
                activity_description=activity_description
            )
            db.add(activity)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log user activity: {e}")
            db.rollback()
