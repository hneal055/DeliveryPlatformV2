from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TelemetryEvent(BaseModel):
    vehicle_id: str = Field(..., description="Unique vehicle identifier")
    ts: datetime = Field(..., description="ISO timestamp of the reading")
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    heading: Optional[float] = Field(None, description="Heading in degrees (0-360)")
    speed: Optional[float] = Field(None, description="Speed in m/s or configured units")
    accuracy: Optional[float] = Field(None, description="Estimated accuracy in meters")
    status: Optional[str] = Field(None, description="Optional status string, e.g. 'delivering', 'idle'")
