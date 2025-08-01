from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import json

Base = declarative_base()

class InterviewLog(Base):
    __tablename__ = "interview_logs"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    transcription = Column(Text, nullable=False)
    candidate_name = Column(String)
    skills = Column(Text)  # Store as JSON string
    years_experience = Column(Integer)
    desired_role = Column(String)
    selected_faq = Column(Text)  # Store as JSON string
    timestamp = Column(DateTime, default=datetime.utcnow)

    def set_skills(self, skills_list):
        self.skills = json.dumps(skills_list)

    def get_skills(self):
        return json.loads(self.skills or "[]")

    def set_selected_faq(self, faq_dict):
        self.selected_faq = json.dumps(faq_dict)

    def get_selected_faq(self):
        return json.loads(self.selected_faq or "{}") 