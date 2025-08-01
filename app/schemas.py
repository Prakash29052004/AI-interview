from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class InterviewLogCreate(BaseModel):
    filename: str
    transcription: str
    candidate_name: Optional[str]
    skills: Optional[List[str]]
    years_experience: Optional[int]
    desired_role: Optional[str]
    selected_faq: Optional[Dict]

class InterviewLogResponse(InterviewLogCreate):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True 