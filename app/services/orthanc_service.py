import httpx
from fastapi import HTTPException

from app.core.config import settings


class OrthancService:

    def get_studies(self):
        try:
            response = httpx.get(
                f"{settings.orthanc_url}/studies",
                auth=(
                    settings.orthanc_username,
                    settings.orthanc_password,
                ),
                timeout=5.0,
            )

            response.raise_for_status()

            return response.json()

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Unable to connect to Orthanc",
            )

        except httpx.HTTPStatusError:
            raise HTTPException(
                status_code=503,
                detail="Orthanc returned an error",
            )

    def get_patients(self):
        try:
            response = httpx.get(
                f"{settings.orthanc_url}/patients",
                auth=(
                    settings.orthanc_username,
                    settings.orthanc_password,
                ),
                timeout=5.0,
            )

            response.raise_for_status()

            return response.json()

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Unable to connect to Orthanc",
            )

        except httpx.HTTPStatusError:
            raise HTTPException(
                status_code=503,
                detail="Orthanc returned an error",
            )

    def get_patient(self, patient_id: str):
        try:
            response = httpx.get(
                f"{settings.orthanc_url}/patients/{patient_id}",
                auth=(
                    settings.orthanc_username,
                    settings.orthanc_password,
                ),
                timeout=5.0,
            )

            response.raise_for_status()

            patient = response.json()

            return {
                "patient_id": patient["MainDicomTags"]["PatientID"],
                "name": patient["MainDicomTags"]["PatientName"],
                "sex": patient["MainDicomTags"]["PatientSex"],
            }

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Unable to connect to Orthanc",
            )

        except httpx.HTTPStatusError:
            raise HTTPException(
                status_code=404,
                detail="Patient not found",
            )

    def get_patient_studies(self, patient_id: str):
        try:
            response = httpx.get(
                f"{settings.orthanc_url}/patients/{patient_id}",
                auth=(
                    settings.orthanc_username,
                    settings.orthanc_password,
                ),
                timeout=5.0,
            )

            response.raise_for_status()

            patient = response.json()

            return [
                {
                    "study_id": study_id,
                }
                for study_id in patient["Studies"]
            ]

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Unable to connect to Orthanc",
            )

        except httpx.HTTPStatusError:
            raise HTTPException(
                status_code=404,
                detail="Patient not found",
            )

    def get_study(self, study_id: str):
        try:
            response = httpx.get(
                f"{settings.orthanc_url}/studies/{study_id}",
                auth=(
                    settings.orthanc_username,
                    settings.orthanc_password,
                ),
                timeout=5.0,
            )

            response.raise_for_status()

            study = response.json()

            return {
                "study_id": study["ID"],
                "study_date": study["MainDicomTags"]["StudyDate"],
                "study_description": study["MainDicomTags"]["StudyDescription"],
                "accession_number": study["MainDicomTags"]["AccessionNumber"],
            }

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Unable to connect to Orthanc",
            )

        except httpx.HTTPStatusError:
            raise HTTPException(
                status_code=404,
                detail="Study not found",
            )

    def get_study_series(self, study_id: str):
        try:
            response = httpx.get(
                f"{settings.orthanc_url}/studies/{study_id}",
                auth=(
                    settings.orthanc_username,
                    settings.orthanc_password,
                ),
                timeout=5.0,
            )

            response.raise_for_status()

            study = response.json()

            return [
                {
                    "series_id": series_id,
                }
                for series_id in study["Series"]
            ]

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Unable to connect to Orthanc",
            )

        except httpx.HTTPStatusError:
            raise HTTPException(
                status_code=404,
                detail="Study not found",
            )

    def get_series(self, series_id: str):
        try:
            response = httpx.get(
                f"{settings.orthanc_url}/series/{series_id}",
                auth=(
                    settings.orthanc_username,
                    settings.orthanc_password,
                ),
                timeout=5.0,
            )

            response.raise_for_status()

            series = response.json()

            return {
                "series_id": series["ID"],
                "modality": series["MainDicomTags"]["Modality"],
                "body_part": series["MainDicomTags"]["BodyPartExamined"],
                "series_description": series["MainDicomTags"]["SeriesDescription"],
            }

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Unable to connect to Orthanc",
            )

        except httpx.HTTPStatusError:
            raise HTTPException(
                status_code=404,
                detail="Series not found",
            )

    def get_series_instances(self, series_id: str):
        try:
            response = httpx.get(
                f"{settings.orthanc_url}/series/{series_id}",
                auth=(
                    settings.orthanc_username,
                    settings.orthanc_password,
                ),
                timeout=5.0,
            )

            response.raise_for_status()

            series = response.json()

            return [
                {
                    "instance_id": instance_id,
                }
                for instance_id in series["Instances"]
            ]

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Unable to connect to Orthanc",
            )

        except httpx.HTTPStatusError:
            raise HTTPException(
                status_code=404,
                detail="Series not found",
            )