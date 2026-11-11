
import httpx

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response


app = FastAPI(
    title="ZFP API Gateway",
    version="1.0.0",
)


AUTH_SERVICE_URL = "http://127.0.0.1:8001"
IMAGING_SERVICE_URL = "http://127.0.0.1:8002"


@app.get("/health")
def health_check():
    return {
        "service": "api-gateway",
        "status": "healthy",
    }


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def gateway(request: Request, path: str):

    request_path = f"/{path}"

    if (
        request_path == "/api/v1/users"
        or request_path.startswith("/api/v1/auth/")
    ):
        service_url = AUTH_SERVICE_URL

    elif request_path.startswith(
        (
            "/api/v1/studies",
            "/api/v1/patients",
            "/api/v1/series",
        )
    ):
        service_url = IMAGING_SERVICE_URL

    else:
        raise HTTPException(
            status_code=404,
            detail="API endpoint not found",
        )

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {
            "host",
            "content-length",
            "connection",
        }
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=f"{service_url}{request.url.path}",
                params=request.query_params,
                content=await request.body(),
                headers=headers,
            )

        excluded_headers = {
            "content-length",
            "transfer-encoding",
            "connection",
            "content-encoding",
        }

        response_headers = {
            key: value
            for key, value in response.headers.items()
            if key.lower() not in excluded_headers
        }

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Backend service is unavailable",
        )
