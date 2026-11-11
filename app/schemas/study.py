from pydantic import BaseModel


class StudyResponse(BaseModel):
    study_id: str
    study_date: str
    study_description: str
    accession_number: str


class PatientStudyResponse(BaseModel):
    study_id: str