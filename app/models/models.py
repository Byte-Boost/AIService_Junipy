from typing import List, Literal, Optional
from pydantic import BaseModel


class UserHistory(BaseModel):
    id: str
    userId: str
    chatId: Optional[str]
    userMessage: str
    aiResponse: str
    timestamp: str


class UserInfo(BaseModel):
    id: str = ""
    userId: str = ""
    name : str = ""
    birthDate: str = ""
    sex: str = ""
    occupation: str = ""
    consultationReason: str = ""
    weight: int = 0
    height: int = 0
    healthConditions: List[str] = []
    allergies: List[str] = []
    surgeries: List[str] = []
    activityType: str = ""
    activityFrequency: str = ""
    activityDuration: str = ""
    sleepQuality: str = ""
    wakeDuringNight: str = ""
    bowelFrequency: str = ""
    stressLevel: str = ""
    alcoholConsumption: str = ""
    smoking: str = ""
    hydrationLevel: str = ""
    takesMedication: str = ""
    medicationDetails: str = ""


UserInfoKeys = Literal[*UserInfo.__annotations__.keys()]


class IndevChatRequest(BaseModel):
    prompt: str


class ChatRequest(BaseModel):
    prompt: str
    userID: str
    chatID: Optional[str]
    userInfo: Optional[UserInfo]
    userHistory: Optional[List[UserHistory]]
