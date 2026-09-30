from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.analysis import router

app = FastAPI(title="AlgoViz Backend API", version="1.0.0")
app.include_router(router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"success": False,
        "error": {"code": "INVALID_REQUEST", "message": "Request body or parameters are invalid"}})


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"success": False,
        "error": {"code": "INTERNAL_ERROR", "message": "An internal server error occurred"}})

