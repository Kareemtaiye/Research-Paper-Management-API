import re
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from asyncpg.exceptions import UniqueViolationError
from h11 import Request
from app.exceptions.schemas import ErrorResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


# instead of relying on decorators in another module
def register_exception_handlers(app):  # explicit reg(to avoid silent import issues)
    @app.exception_handler(UniqueViolationError)
    async def duplicate_db_value_handler(request, exc: UniqueViolationError):
        match = re.search(
            r"[\w .]+\(([^)]+)\)=\(([^)]+)\)[\w .]+", exc.detail, flags=re.IGNORECASE
        )
        message = "Duplicate value violates a unique constraint."
        details = {"constraint": exc.constraint_name}

        if match:
            field, value = match.groups()
            message = f"This {field} value: {value} already exists."
            details.update({"field": field, "value": value})

        err_obj = ErrorResponse(
            status="error", code=400, message=message, details=details
        )

        return JSONResponse(status_code=err_obj.code, content=err_obj.model_dump())

    @app.exception_handler(RequestValidationError)
    async def req_validation_exception_handler(request, exc: RequestValidationError):

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

        return JSONResponse(status_code=500, content=err_obj.model_dump())

    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ):
        return JSONResponse(
            status_code=exc.status_code, content=jsonable_encoder(exc.detail)
        )
