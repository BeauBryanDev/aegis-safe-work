from fastapi import Request, status
from fastapi.responses import JSONResponse


# Base Exception

class AegisException(Exception):
    """Base exception for all Aegis-Safe-Work domain errors."""
 
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message     = message
        self.status_code = status_code
        super().__init__(message)
 
 
    def to_dict(self) -> dict:
        return {
            "message": self.message,
            "status_code": self.status_code,
        }
 
    def to_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=self.status_code,
            content=self.to_dict(),
        )
        
        

# HTTP Exceptions

class HTTPException(AegisException):
    """Base exception for all HTTP-related errors."""
 
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message     = message
        self.status_code = status_code
        super().__init__(message, status_code)
 
 
class NotFoundException(HTTPException):
    """Exception for when a resource is not found."""
 
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_404_NOT_FOUND)
 
 
class BadRequestException(HTTPException):
    """Exception for when a request is malformed."""
 
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)
 
 
class UnauthorizedException(HTTPException):
    """Exception for when a request lacks valid authentication credentials."""
 
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)
 
 
class ForbiddenException(HTTPException):
    """Exception for when a request is authenticated but lacks permissions."""
 
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_403_FORBIDDEN)
 
 
class NotAcceptableException(HTTPException):
    """Exception for when a request's Accept header is not supported."""
 
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_406_NOT_ACCEPTABLE)
 
 
class ConflictException(HTTPException):
    """Exception for when a request conflicts with the current state of the target resource."""
 
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_409_CONFLICT)
 
 
class InternalServerException(HTTPException):
    """Exception for when an internal server error occurs."""
 
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)
 
 
class ServiceUnavailableException(HTTPException):
    """Exception for when the service is temporarily unavailable."""
 
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE)
 
 
# Custom Exceptions

class InvalidModelException(AegisException):
    """Exception for when an invalid model is requested."""
 
    def __init__(self, model: str):
        super().__init__(f"Invalid model: {model}")
        
        
# Model Inference Error
class ModelNotLoadedError(AegisException):
    """Raised when an ONNX session is requested before startup load completes."""
 
    def __init__(self, model_name: str):
        super().__init__(
            message=f"Model '{model_name}' is not loaded. The server may still be starting up.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        

class InferenceError(AegisException):
    """Raised when an ONNX Runtime inference call fails or returns malformed output."""
 
    def __init__(self, model_name: str, detail: str):
        super().__init__(
            message=f"Inference failed for model '{model_name}': {detail}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
 
 
class InvalidFrameError(AegisException):
    """Raised when an incoming frame cannot be decoded or has invalid shape/format."""
 
    def __init__(self, detail: str):
        super().__init__(
            message=f"Invalid frame received: {detail}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
 
 
# Tracking / Bufffer Errors


class InferenceError(AegisException):
    """Raised when an ONNX Runtime inference call fails or returns malformed output."""
 
    def __init__(self, model_name: str, detail: str):
        super().__init__(
            message=f"Inference failed for model '{model_name}': {detail}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
 
 
class InvalidFrameError(AegisException):
    """Raised when an incoming frame cannot be decoded or has invalid shape/format."""
 
    def __init__(self, detail: str):
        super().__init__(
            message=f"Invalid frame received: {detail}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
 
 
# Tracking Buffer /Errors 

class TrackNotFoundError(AegisException):
    """Raised when a frame buffer or fall inference is requested for an unknown track_id."""
 
    def __init__(self, track_id: int):
        super().__init__(
            message=f"Track ID '{track_id}' not found in active tracker state.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
 
 
class FrameBufferNotReadyError(AegisException):
    """Raised when fall inference is attempted before the buffer has N_FRAMES collected."""
 
    def __init__(self, track_id: int, current_count: int, required: int):
        super().__init__(
            message=(
                f"Frame buffer for track '{track_id}' has {current_count}/{required} "
                f"frames. Fall inference is not yet available for this track."
            ),
            status_code=status.HTTP_409_CONFLICT,
        )
 

# Data Persistence Errors


class AlertPersistenceError(AegisException):
    """Raised when an alert fails to write to PostgreSQL."""
 
    def __init__(self, detail: str):
        super().__init__(
            message=f"Failed to persist alert: {detail}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
 
 
class RecordNotFoundError(AegisException):
    """Raised when a requested DB record (alert, detection, location) does not exist."""
 
    def __init__(self, resource: str, identifier):
        super().__init__(
            message=f"{resource} with id '{identifier}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


# Exception Handlers Registered on FastAPI Instance


async def aegis_exception_handler(request: Request, exc: AegisException) -> JSONResponse:
    """
    Catches all AegisException subclasses and returns a structured JSON error.
    Registered in main.py: app.add_exception_handler(AegisException, aegis_exception_handler)
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error":      exc.__class__.__name__,
            "message":    exc.message,
            "path":       str(request.url.path),
        },
    )
 
 
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Fallback handler for any uncaught exception. Prevents raw tracebacks
    from leaking to clients in production. Logging of the actual exception
    should happen via middleware or the logger before this handler returns.
    Registered in main.py: app.add_exception_handler(Exception, unhandled_exception_handler)
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error":   "InternalServerError",
            "message": "An unexpected error occurred. Please try again or contact support.",
            "path":    str(request.url.path),
        },
    )
 