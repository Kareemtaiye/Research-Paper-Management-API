import re

from fastapi.requests import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from asyncpg.exceptions import UniqueViolationError, DataError
from jwt.exceptions import DecodeError, ExpiredSignatureError as ExpiredJWTError
from pydantic_core import ValidationError
from app.exceptions.schemas import ErrorResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.logger import logger


# instead of relying on decorators in another module
def register_exception_handlers(app):  # explicit reg(to avoid silent import issues)
    @app.exception_handler(UniqueViolationError)
    def duplicate_db_value_handler(request, exc: UniqueViolationError):
        match = re.search(
            r"[\w .]+\(([^)]+)\)=\(([^)]+)\)[\w .]+", exc.detail, flags=re.IGNORECASE
        )
        message = "Duplicate value violates a unique constraint."
        # details = {"constraint": exc.constraint_name}
        details = {}

        if match:
            field, value = match.groups()
            message = f"This {field} value: {value} already exists."
            details.update({"field": field, "value": value})

        err_obj = ErrorResponse(
            status="error", code=400, message=message, details=details
        )

        logger.error(
            f"Trying to insert duplicate value for unique column in db: {exc} "
        )

        return JSONResponse(status_code=err_obj.code, content=err_obj.model_dump())

    @app.exception_handler(RequestValidationError)
    def req_validation_exception_handler(request: Request, exc: RequestValidationError):

        details = [
            {
                "api_param": err["loc"][0] or None,
                "field": err["loc"][1] or "",
                "input": err["input"],
                "msg": err["msg"],
            }
            for err in exc.errors()
        ]

        err_obj = ErrorResponse(
            status="error",
            code=400,
            message="Inputs validation failed",
            details=details,
        )

        logger.error(f"Pydantic validation failed for user input: {exc}")

        return JSONResponse(status_code=500, content=err_obj.model_dump())

    @app.exception_handler(ValidationError)
    def req_validation_exception_handler(request: Request, exc: RequestValidationError):
        details = [
            {
                "field": err["loc"][0] or "",
                "input": err["input"],
                "msg": err["msg"],
            }
            for err in exc.errors()
        ]

        err_obj = ErrorResponse(
            status="error",
            code=400,
            message="Inputs validation failed",
            details=details,
        )

        logger.error(f"Pydantic validation failed for user input: {exc.errors()}")

        return JSONResponse(status_code=500, content=err_obj.model_dump())

    @app.exception_handler(StarletteHTTPException)
    def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):

        return JSONResponse(
            status_code=exc.status_code, content=jsonable_encoder(exc.detail)
        )

    @app.exception_handler(ExpiredJWTError)
    def expired_jwt_handler(request: Request, exc: ExpiredJWTError):
        client_ip = request.client.host if request.client else "unknown"
        logger.error(f"Access token expired for request. IP: {client_ip}")

        return JSONResponse(
            status_code=400,
            content=jsonable_encoder(
                ErrorResponse(code=400, message="Access token expired")
            ),
        )

    @app.exception_handler(DecodeError)
    def invalid_jwt_handler(request: Request, exc: ExpiredJWTError):
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(f"Invalid Access token attempt from. IP: {client_ip}")

        return JSONResponse(
            status_code=400,
            content=jsonable_encoder(
                ErrorResponse(code=400, message="Invalid access token")
            ),
        )

    @app.exception_handler(DataError)
    def db_insertion_data_error_handler(request: Request, exc: DataError):
        logger.warning(f"Database insertion error: {exc}")

        return JSONResponse(
            status_code=400,
            content=jsonable_encoder(ErrorResponse(code=400, message=str(exc))),
        )
