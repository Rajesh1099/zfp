from pydantic import BaseModel


class SeriesInstanceResponse(BaseModel):
    instance_id: str