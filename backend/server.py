from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import jwt
import hashlib
import uuid
from bson import ObjectId

# Database setup
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = MongoClient(MONGO_URL)
db = client.learning_tracker

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT setup
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
security = HTTPBearer()

# Pydantic models
class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    position: str
    department: str
    date_of_joining: str
    existing_skills: List[str]
    learning_interests: List[str]
    profile_picture: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class LearningGoal(BaseModel):
    id: str
    title: str
    description: str
    target_completion: str
    status: str = "active"
    created_at: str

class Milestone(BaseModel):
    id: str
    goal_id: str
    user_id: str
    what_learned: str
    learning_source: str
    can_teach_others: bool
    hours_invested: float
    project_certificate_link: Optional[str] = None
    created_at: str
    month_year: str

class GoalCreate(BaseModel):
    title: str
    description: str
    target_completion: str

class MilestoneCreate(BaseModel):
    goal_id: str
    what_learned: str
    learning_source: str
    can_teach_others: bool
    hours_invested: float
    project_certificate_link: Optional[str] = None

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Auth endpoints
@app.post("/api/register")
async def register(user: UserRegister):
    # Check if user exists
    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "full_name": user.full_name,
        "email": user.email,
        "password": hash_password(user.password),
        "position": user.position,
        "department": user.department,
        "date_of_joining": user.date_of_joining,
        "existing_skills": user.existing_skills,
        "learning_interests": user.learning_interests,
        "profile_picture": user.profile_picture,
        "role": "employee",
        "created_at": datetime.utcnow().isoformat()
    }
    
    db.users.insert_one(user_doc)
    
    access_token = create_access_token(data={"sub": user_id})
    return {"access_token": access_token, "token_type": "bearer", "user": {
        "id": user_id,
        "full_name": user.full_name,
        "email": user.email,
        "role": "employee"
    }}

@app.post("/api/login")
async def login(user: UserLogin):
    db_user = db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": db_user["id"]})
    return {"access_token": access_token, "token_type": "bearer", "user": {
        "id": db_user["id"],
        "full_name": db_user["full_name"],
        "email": db_user["email"],
        "role": db_user.get("role", "employee")
    }}

# User profile endpoints
@app.get("/api/profile")
async def get_profile(user_id: str = Depends(get_current_user)):
    user = db.users.find_one({"id": user_id}, {"password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Remove MongoDB ObjectId
    user.pop("_id", None)
    return user

@app.put("/api/profile")
async def update_profile(profile_data: dict, user_id: str = Depends(get_current_user)):
    # Remove sensitive fields
    profile_data.pop("password", None)
    profile_data.pop("id", None)
    profile_data.pop("email", None)
    
    db.users.update_one({"id": user_id}, {"$set": profile_data})
    return {"message": "Profile updated successfully"}

# Goals endpoints
@app.post("/api/goals")
async def create_goal(goal: GoalCreate, user_id: str = Depends(get_current_user)):
    goal_id = str(uuid.uuid4())
    goal_doc = {
        "id": goal_id,
        "user_id": user_id,
        "title": goal.title,
        "description": goal.description,
        "target_completion": goal.target_completion,
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    
    db.goals.insert_one(goal_doc)
    goal_doc.pop("_id", None)
    return goal_doc

@app.get("/api/goals")
async def get_user_goals(user_id: str = Depends(get_current_user)):
    goals = list(db.goals.find({"user_id": user_id}, {"_id": 0}))
    return goals

@app.put("/api/goals/{goal_id}")
async def update_goal(goal_id: str, goal_data: dict, user_id: str = Depends(get_current_user)):
    result = db.goals.update_one(
        {"id": goal_id, "user_id": user_id},
        {"$set": goal_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"message": "Goal updated successfully"}

@app.delete("/api/goals/{goal_id}")
async def delete_goal(goal_id: str, user_id: str = Depends(get_current_user)):
    result = db.goals.delete_one({"id": goal_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"message": "Goal deleted successfully"}

# Milestones endpoints
@app.post("/api/milestones")
async def create_milestone(milestone: MilestoneCreate, user_id: str = Depends(get_current_user)):
    milestone_id = str(uuid.uuid4())
    current_date = datetime.utcnow()
    month_year = current_date.strftime("%Y-%m")
    
    milestone_doc = {
        "id": milestone_id,
        "goal_id": milestone.goal_id,
        "user_id": user_id,
        "what_learned": milestone.what_learned,
        "learning_source": milestone.learning_source,
        "can_teach_others": milestone.can_teach_others,
        "hours_invested": milestone.hours_invested,
        "project_certificate_link": milestone.project_certificate_link,
        "created_at": current_date.isoformat(),
        "month_year": month_year
    }
    
    db.milestones.insert_one(milestone_doc)
    milestone_doc.pop("_id", None)
    return milestone_doc

@app.get("/api/milestones")
async def get_user_milestones(user_id: str = Depends(get_current_user), month: Optional[str] = None):
    query = {"user_id": user_id}
    if month:
        query["month_year"] = month
    
    milestones = list(db.milestones.find(query, {"_id": 0}))
    return milestones

@app.get("/api/milestones/current-month")
async def get_current_month_progress(user_id: str = Depends(get_current_user)):
    current_month = datetime.utcnow().strftime("%Y-%m")
    milestones = list(db.milestones.find({"user_id": user_id, "month_year": current_month}, {"_id": 0}))
    
    total_hours = sum(m["hours_invested"] for m in milestones)
    target_hours = 6
    progress_percentage = min((total_hours / target_hours) * 100, 100)
    
    return {
        "total_hours": total_hours,
        "target_hours": target_hours,
        "progress_percentage": progress_percentage,
        "milestones": milestones,
        "month_year": current_month
    }

@app.put("/api/milestones/{milestone_id}")
async def update_milestone(milestone_id: str, milestone_data: dict, user_id: str = Depends(get_current_user)):
    result = db.milestones.update_one(
        {"id": milestone_id, "user_id": user_id},
        {"$set": milestone_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return {"message": "Milestone updated successfully"}

@app.delete("/api/milestones/{milestone_id}")
async def delete_milestone(milestone_id: str, user_id: str = Depends(get_current_user)):
    result = db.milestones.delete_one({"id": milestone_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return {"message": "Milestone deleted successfully"}

# Resource directory endpoints
@app.get("/api/resources")
async def get_resources():
    # Auto-generate from milestone entries
    pipeline = [
        {"$group": {
            "_id": "$learning_source",
            "count": {"$sum": 1},
            "total_hours": {"$sum": "$hours_invested"},
            "skills": {"$addToSet": "$what_learned"}
        }},
        {"$sort": {"count": -1}}
    ]
    
    resources = list(db.milestones.aggregate(pipeline))
    formatted_resources = []
    
    for resource in resources:
        formatted_resources.append({
            "id": str(uuid.uuid4()),
            "name": resource["_id"],
            "usage_count": resource["count"],
            "total_hours": resource["total_hours"],
            "skills_taught": resource["skills"][:5],  # Limit to top 5 skills
            "category": "auto-generated"
        })
    
    return formatted_resources

# Dashboard stats
@app.get("/api/dashboard/stats")
async def get_dashboard_stats(user_id: str = Depends(get_current_user)):
    current_month = datetime.utcnow().strftime("%Y-%m")
    
    # Current month progress
    current_milestones = list(db.milestones.find({"user_id": user_id, "month_year": current_month}))
    current_hours = sum(m["hours_invested"] for m in current_milestones)
    
    # Total stats
    total_milestones = db.milestones.count_documents({"user_id": user_id})
    total_hours = sum(m["hours_invested"] for m in db.milestones.find({"user_id": user_id}))
    active_goals = db.goals.count_documents({"user_id": user_id, "status": "active"})
    
    # Recent milestones
    recent_milestones = list(db.milestones.find(
        {"user_id": user_id}, 
        {"_id": 0}
    ).sort([("created_at", -1)]).limit(5))
    
    return {
        "current_month_hours": current_hours,
        "target_hours": 6,
        "progress_percentage": min((current_hours / 6) * 100, 100),
        "total_milestones": total_milestones,
        "total_hours": total_hours,
        "active_goals": active_goals,
        "recent_milestones": recent_milestones
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)