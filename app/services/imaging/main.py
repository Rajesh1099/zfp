
from fastapi import Depends, FastAPI

from app.core.roles import UserRole
from app.schemas.instance import SeriesInstanceResponse
from app.schemas.patient import PatientResponse
from app.schemas.series import (
    SeriesResponse,
    StudySeriesResponse,
)
from app.schemas.study import (
    PatientStudyResponse,
    StudyResponse,
)
from app.services.imaging.dependencies import require_role
from app.services.orthanc_service import OrthancService
from app.api.dependencies import get_orthanc_service


app = FastAPI(
    title="ZFP Imaging Service",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {
        "service": "imaging",
        "status": "healthy",
    }


@app.get("/api/v1/studies")
def get_studies_endpoint(
    current_user: dict = Depends(
        require_role(UserRole.ADMIN, UserRole.RADIOLOGIST)
    ),
    orthanc_service: OrthancService = Depends(get_orthanc_service),
):
    return orthanc_service.get_studies()


@app.get("/api/v1/patients")
def get_patients(
    current_user: dict = Depends(
        require_role(UserRole.ADMIN, UserRole.RADIOLOGIST)
    ),
    orthanc_service: OrthancService = Depends(get_orthanc_service),
):
    return orthanc_service.get_patients()


@app.get(
    "/api/v1/patients/{patient_id}",
    response_model=PatientResponse,
)
def get_patient(
    patient_id: str,
    current_user: dict = Depends(
        require_role(UserRole.ADMIN, UserRole.RADIOLOGIST)
    ),
    orthanc_service: OrthancService = Depends(get_orthanc_service),
):
    return orthanc_service.get_patient(patient_id)


@app.get(
    "/api/v1/patients/{patient_id}/studies",
    response_model=list[PatientStudyResponse],
)
def get_patient_studies(
    patient_id: str,
    current_user: dict = Depends(
        require_role(UserRole.ADMIN, UserRole.RADIOLOGIST)
    ),
    orthanc_service: OrthancService = Depends(get_orthanc_service),
):
    return orthanc_service.get_patient_studies(patient_id)


@app.get(
    "/api/v1/studies/{study_id}",
    response_model=StudyResponse,
)
def get_study(
    study_id: str,
    current_user: dict = Depends(
        require_role(UserRole.ADMIN, UserRole.RADIOLOGIST)
    ),
    orthanc_service: OrthancService = Depends(get_orthanc_service),
):
    return orthanc_service.get_study(study_id)


@app.get(
    "/api/v1/studies/{study_id}/series",
    response_model=list[StudySeriesResponse],
)
def get_study_series(
    study_id: str,
    current_user: dict = Depends(
        require_role(UserRole.ADMIN, UserRole.RADIOLOGIST)
    ),
    orthanc_service: OrthancService = Depends(get_orthanc_service),
):
    return orthanc_service.get_study_series(study_id)


@app.get(
    "/api/v1/series/{series_id}",
    response_model=SeriesResponse,
)
def get_series(
    series_id: str,
    current_user: dict = Depends(
        require_role(UserRole.ADMIN, UserRole.RADIOLOGIST)
    ),
    orthanc_service: OrthancService = Depends(get_orthanc_service),
):
    return orthanc_service.get_series(series_id)


@app.get(
    "/api/v1/series/{series_id}/instances",
    response_model=list[SeriesInstanceResponse],
)
def get_series_instances(
    series_id: str,
    current_user: dict = Depends(
        require_role(UserRole.ADMIN, UserRole.RADIOLOGIST)
    ),
    orthanc_service: OrthancService = Depends(get_orthanc_service),
):
    return orthanc_service.get_series_instances(series_id)
