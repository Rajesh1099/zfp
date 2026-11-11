from pydantic import BaseModel


class SeriesResponse(BaseModel):
    series_id: str
    modality: str
    body_part: str
    series_description: str


class StudySeriesResponse(BaseModel):
    series_id: str