from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class PredictionResponse(BaseModel):
    id: int
    model: str
    city: str
    district: int
    hour: int
    cost: float
    status: str
    result: Optional[str]
    timestamp: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }
    )

class PredictionHistoryResponse(BaseModel):
    history: list[PredictionResponse]

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }
    )


class NYCPredictionRequest(BaseModel):
    district: int

    model_config = ConfigDict()

class HistoryRequest(BaseModel):
    amount: Optional[int] = 5
