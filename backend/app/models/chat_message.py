from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.core.database import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    sender = Column(String(50), nullable=False)  # patient, ai_assistant, system
    language = Column(String(50), default="English")
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=True)  # English translation for clinical team
    is_voice = Column(Boolean, default=False)
    audio_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

