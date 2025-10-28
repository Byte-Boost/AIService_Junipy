from typing import List, Optional
from pydantic import BaseModel


class UserHistory(BaseModel):
    id: str
    userId: str
    chatId: Optional[str]
    userMessage: str
    aiResponse: str
    timestamp: str


class UserInfo(BaseModel):
    id: str
    userId: str
    birthDate: str
    sex: str
    occupation: str
    consultationReason: str
    healthConditions: List[str]
    allergies: List[str]
    surgeries: List[str]
    activityType: str
    activityFrequency: str
    activityDuration: str
    sleepQuality: str
    wakeDuringNight: str
    bowelFrequency: str
    stressLevel: str
    alcoholConsumption: str
    smoking: str
    hydrationLevel: str
    takesMedication: str
    medicationDetails: str


class ChatRequest(BaseModel):
    prompt: str
    userID: str
    chatID: Optional[str]
    userInfo: Optional[UserInfo]
    userHistory: Optional[List[UserHistory]]
