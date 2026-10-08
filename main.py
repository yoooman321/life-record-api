from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from life_record_api.exceptions import (
    validation_exception_handler,
    http_exception_handler,
    app_exception_handler,
    AppException,
)
from life_record_api.responses import EnvelopeJSONResponse
from life_record_api.routers.accounting import router as accounting_router
from life_record_api.routers.user import router as user_router

app = FastAPI(default_response_class=EnvelopeJSONResponse)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.include_router(accounting_router)
app.include_router(user_router)


@app.get("/")
def read_root():
    return {"status": "OK"}
