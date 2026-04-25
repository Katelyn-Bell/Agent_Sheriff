from __future__ import annotations

from http import HTTPStatus

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else HTTPStatus(exc.status_code).phrase
        return error_response(exc.status_code, _code_for_status(exc.status_code), message)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, _exc: RequestValidationError) -> JSONResponse:
        return error_response(422, "VALIDATION_ERROR", "Request validation failed.")


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


def _code_for_status(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).phrase.upper().replace(" ", "_").replace("-", "_")
    except ValueError:
        return "HTTP_ERROR"
