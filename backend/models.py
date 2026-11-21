from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db
class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(255),unique=True,nullable=False,index=True)
    password_hash=db.Column(db.String(255),nullable=False)
    timezone=db.Column(db.String(80),nullable=False,default="Asia/Kolkata")
    created_at=db.Column(db.DateTime,default=lambda:datetime.now(timezone.utc),nullable=False)
    def set_password(self,p): self.password_hash=generate_password_hash(p)
    def check_password(self,p): return check_password_hash(self.password_hash,p)
class Routine(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False,index=True)
    name=db.Column(db.String(100),nullable=False)
    category=db.Column(db.String(30),nullable=False)
    description=db.Column(db.String(250),default="")
    target_per_week=db.Column(db.Integer,default=7)
    active=db.Column(db.Boolean,default=True,nullable=False)
    created_at=db.Column(db.DateTime,default=lambda:datetime.now(timezone.utc),nullable=False)
class Completion(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False,index=True)
    routine_id=db.Column(db.Integer,db.ForeignKey("routine.id"),nullable=False,index=True)
    local_date=db.Column(db.String(10),nullable=False,index=True)
    completed=db.Column(db.Boolean,default=True,nullable=False)
    updated_at=db.Column(db.DateTime,default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc))
    __table_args__=(db.UniqueConstraint("user_id","routine_id","local_date",name="uq_completion_day_routine"),)
class Note(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False,index=True)
    routine_id=db.Column(db.Integer,db.ForeignKey("routine.id"),nullable=True)
    local_date=db.Column(db.String(10),nullable=False,index=True)
    title=db.Column(db.String(160),nullable=False,default="Daily note")
    content=db.Column(db.Text,nullable=False)
    created_at=db.Column(db.DateTime,default=lambda:datetime.now(timezone.utc),nullable=False)
    updated_at=db.Column(db.DateTime,default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc))
