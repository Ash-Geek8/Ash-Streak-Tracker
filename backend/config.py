import os
class Config:
    SECRET_KEY=os.getenv("SECRET_KEY","development-only-change-me")
    SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL","sqlite:///ash_streak.db").replace("postgres://","postgresql://",1)
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    SESSION_COOKIE_HTTPONLY=True
    SESSION_COOKIE_SAMESITE="Lax"
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip().lower()
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE","false").lower()=="true"
    REMEMBER_COOKIE_HTTPONLY=True
    REMEMBER_COOKIE_SAMESITE="Lax"
    ALLOW_REGISTRATION=os.getenv("ALLOW_REGISTRATION","true").lower()=="true"
    DEFAULT_TIMEZONE=os.getenv("DEFAULT_TIMEZONE","Asia/Kolkata")
    CHROMA_DIR=os.getenv("CHROMA_DIR","instance/chroma")
    CORS_ORIGINS=[x.strip() for x in os.getenv("CORS_ORIGINS","http://localhost:3000").split(",") if x.strip()]
    MAX_CONTENT_LENGTH=2*1024*1024
