from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_serializer


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

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('timestamp')
    def format_timestamp(self, dt: datetime) -> str:
        return dt.strftime('%Y-%m-%d %H:%M:%S')

class PredictionHistoryResponse(BaseModel):
    history: list[PredictionResponse]

    model_config = ConfigDict(from_attributes=True)


class NYCPredictionRequest(BaseModel):
    district: int

    model_config = ConfigDict()

class HistoryRequest(BaseModel):
    amount: Optional[int] = 5
