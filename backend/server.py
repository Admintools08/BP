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
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage

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

# AI setup
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

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

class AIRecommendation(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    skill_category: str
    recommended_resources: List[str]
    difficulty_level: str
    estimated_hours: int
    priority_score: int
    created_at: str

# AI Service for learning recommendations
class LearningRecommendationService:
    def __init__(self):
        self.api_key = OPENAI_API_KEY
    
    async def generate_recommendations(self, user_profile: dict, goals: list, milestones: list) -> List[dict]:
        if not self.api_key:
            return []
        
        try:
            # Create personalized learning context
            context = self._build_learning_context(user_profile, goals, milestones)
            
            # Initialize AI chat
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"learning-rec-{user_profile['id']}",
                system_message="""You are an expert learning and career development advisor. 
                Generate personalized learning recommendations based on the user's profile, goals, and progress.
                
                Respond with EXACTLY 5 recommendations in JSON format:
                [
                  {
                    "title": "Short specific skill/topic title",
                    "description": "Brief 2-3 sentence description of why this is valuable",
                    "skill_category": "Category like 'Technical', 'Leadership', 'Design', etc.",
                    "recommended_resources": ["Resource 1", "Resource 2", "Resource 3"],
                    "difficulty_level": "Beginner/Intermediate/Advanced",
                    "estimated_hours": 8,
                    "priority_score": 85
                  }
                ]
                
                Make recommendations practical, specific, and aligned with their career trajectory."""
            ).with_model("openai", "gpt-4o")
            
            user_message = UserMessage(text=context)
            
            # Get AI response
            response = await chat.send_message(user_message)
            
            # Parse and validate response
            recommendations = self._parse_ai_response(response, user_profile['id'])
            return recommendations
            
        except Exception as e:
            print(f"AI recommendation error: {str(e)}")
            return []
    
    def _build_learning_context(self, user_profile: dict, goals: list, milestones: list) -> str:
        skills_learned = []
        recent_sources = set()
        total_hours = 0
        
        for milestone in milestones[-10:]:  # Last 10 milestones
            skills_learned.append(milestone.get('what_learned', ''))
            recent_sources.add(milestone.get('learning_source', ''))
            total_hours += milestone.get('hours_invested', 0)
        
        active_goal_titles = [goal.get('title', '') for goal in goals if goal.get('status') == 'active']
        
        context = f"""
        EMPLOYEE PROFILE:
        - Name: {user_profile.get('full_name', '')}
        - Position: {user_profile.get('position', '')}
        - Department: {user_profile.get('department', '')}
        - Experience: {user_profile.get('date_of_joining', '')}
        - Current Skills: {', '.join(user_profile.get('existing_skills', []))}
        - Learning Interests: {', '.join(user_profile.get('learning_interests', []))}
        
        CURRENT LEARNING GOALS:
        {', '.join(active_goal_titles) if active_goal_titles else 'No active goals'}
        
        RECENT LEARNING ACTIVITY:
        - Recent Skills Learned: {'; '.join(skills_learned[-5:]) if skills_learned else 'No recent activity'}
        - Learning Sources Used: {', '.join(list(recent_sources)) if recent_sources else 'None'}
        - Total Learning Hours: {total_hours} hours
        
        Please recommend 5 personalized learning opportunities that would:
        1. Build on their existing skills and interests
        2. Advance their career in their current role/department
        3. Introduce complementary skills they haven't explored
        4. Include both technical and soft skills where appropriate
        5. Consider their learning pace and current workload
        """
        
        return context
    
    def _parse_ai_response(self, response: str, user_id: str) -> List[dict]:
        try:
            import json
            # Extract JSON from response
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean.replace('```json', '').replace('```', '').strip()
            elif response_clean.startswith('```'):
                response_clean = response_clean.replace('```', '').strip()
            
            recommendations_data = json.loads(response_clean)
            
            recommendations = []
            for idx, rec in enumerate(recommendations_data[:5]):  # Limit to 5
                recommendation = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "title": rec.get('title', f'Learning Recommendation {idx + 1}'),
                    "description": rec.get('description', 'Personalized learning recommendation'),
                    "skill_category": rec.get('skill_category', 'General'),
                    "recommended_resources": rec.get('recommended_resources', []),
                    "difficulty_level": rec.get('difficulty_level', 'Intermediate'),
                    "estimated_hours": rec.get('estimated_hours', 8),
                    "priority_score": rec.get('priority_score', 75),
                    "created_at": datetime.utcnow().isoformat()
                }
                recommendations.append(recommendation)
            
            return recommendations
        except Exception as e:
            print(f"Error parsing AI response: {str(e)}")
            # Fallback recommendations
            return self._fallback_recommendations(user_id)
    
    def _fallback_recommendations(self, user_id: str) -> List[dict]:
        """Fallback recommendations if AI fails"""
        fallback_recs = [
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "title": "Time Management & Productivity",
                "description": "Essential skills for any professional to maximize efficiency and reduce stress.",
                "skill_category": "Productivity",
                "recommended_resources": ["Getting Things Done book", "Pomodoro Technique", "Notion workspace setup"],
                "difficulty_level": "Beginner",
                "estimated_hours": 6,
                "priority_score": 85,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "title": "Communication & Presentation Skills",
                "description": "Improve your ability to communicate ideas clearly and present with confidence.",
                "skill_category": "Soft Skills",
                "recommended_resources": ["Toastmasters", "TED Talks on communication", "Presentation design courses"],
                "difficulty_level": "Intermediate",
                "estimated_hours": 10,
                "priority_score": 80,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        return fallback_recs

# Initialize AI service
ai_service = LearningRecommendationService()

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

# AI Recommendations endpoints
@app.get("/api/ai-recommendations")
async def get_ai_recommendations(user_id: str = Depends(get_current_user)):
    """Get personalized AI learning recommendations"""
    try:
        # Get user profile, goals, and milestones
        user_profile = db.users.find_one({"id": user_id}, {"password": 0, "_id": 0})
        goals = list(db.goals.find({"user_id": user_id}, {"_id": 0}))
        milestones = list(db.milestones.find({"user_id": user_id}, {"_id": 0}).sort([("created_at", -1)]))
        
        if not user_profile:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate recommendations using AI
        recommendations = await ai_service.generate_recommendations(user_profile, goals, milestones)
        
        # Store recommendations in database for caching
        if recommendations:
            # Clear old recommendations
            db.ai_recommendations.delete_many({"user_id": user_id})
            # Insert new ones
            for rec in recommendations:
                db.ai_recommendations.insert_one(rec)
        
        return recommendations
        
    except Exception as e:
        print(f"Error generating recommendations: {str(e)}")
        # Return cached recommendations if available
        cached = list(db.ai_recommendations.find({"user_id": user_id}, {"_id": 0}))
        if cached:
            return cached
        else:
            # Return basic fallback recommendations
            return ai_service._fallback_recommendations(user_id)

@app.post("/api/ai-recommendations/refresh")
async def refresh_ai_recommendations(user_id: str = Depends(get_current_user)):
    """Force refresh AI recommendations"""
    # Clear cached recommendations
    db.ai_recommendations.delete_many({"user_id": user_id})
    
    # Get fresh recommendations
    return await get_ai_recommendations(user_id)

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