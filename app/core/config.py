
from pathlib import Path
from typing import List
 
from pydantic import AnyUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
 
 
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
 
 
    # App
    APP_NAME: str        = "Aegis-Safe-Work"
    APP_VERSION: str     = "1.0.0"
    DEBUG: bool          = False
    WORKERS: int         = 1
 
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
 
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
 
    # Database — postgresql+asyncpg via RDS / EC2 bastion
    DATABASE_URL: str = (
        "postgresql+asyncpg://user:password@localhost:5432/aegis_safe_work"
    )
    DB_POOL_SIZE: int       = 5
    DB_MAX_OVERFLOW: int    = 10
    DB_POOL_TIMEOUT: int    = 30
    DB_ECHO: bool           = False
 
    # ONNX Model paths — relative to project root: ../ml/models/
    MODELS_DIR: Path = Path(__file__).resolve().parents[2] / "ml" / "models"
 
    @property
    def PPE_MODEL_PATH(self) -> Path:
        return self.MODELS_DIR / "ppe_yolov11s.onnx"
 
    @property
    def FALL_MODEL_PATH(self) -> Path:
        return self.MODELS_DIR / "fall_detector_optimized.onnx"
 
    @property
    def FIRE_SMOKE_MODEL_PATH(self) -> Path:
        return self.MODELS_DIR / "fire_smoke_yolov8n.onnx"
 
    # ONNX Runtime execution providers
    ORT_PROVIDERS: List[str] = ["CUDAExecutionProvider", "CPUExecutionProvider"]
 
    # PPE Detector — YOLOv11s
    PPE_CONF_THRESHOLD: float   = 0.35
    PPE_IOU_THRESHOLD: float    = 0.45
    PPE_INPUT_SIZE: int         = 640
 
    # Class indices — must match training label map
    PPE_CLASS_HELMET: int       = 0
    PPE_CLASS_GLOVES: int       = 1
    PPE_CLASS_VEST: int         = 2
    PPE_CLASS_BOOTS: int        = 3
    PPE_CLASS_GOGGLES: int      = 4
    PPE_CLASS_NONE: int         = 5
    PPE_CLASS_PERSON: int       = 6
    PPE_CLASS_NO_HELMET: int    = 7
    PPE_CLASS_NO_GOGGLE: int    = 8
    PPE_CLASS_NO_GLOVES: int    = 9
    PPE_CLASS_NO_BOOTS: int     = 10
 
    # Post-processing caps (overcounting correction)
    MAX_GLOVES_PER_PERSON: int  = 2
    MAX_BOOTS_PER_PERSON: int   = 2
 
    # Fall Detector — EfficientNet-Lite0 + Attention MLP
    FALL_THRESHOLD: float       = 0.65
    N_FRAMES: int               = 16
    IMG_SIZE: int               = 224
 
    # ImageNet normalization (must match ETL Stage 2)
    IMAGENET_MEAN: List[float]  = [0.485, 0.456, 0.406]
    IMAGENET_STD: List[float]   = [0.229, 0.224, 0.225]
 
    # Tracker (ByteTrack / SORT)
    TRACKER_MAX_AGE: int        = 30    # frames before track is dropped
    TRACKER_MIN_HITS: int       = 3     # min detections before track confirmed
    TRACKER_IOU_THRESHOLD: float = 0.3
 
    # Frame buffer — fall detection sliding window
    FRAME_BUFFER_SIZE: int      = 16    # must equal N_FRAMES
    FRAME_BUFFER_STEP: int      = 8     # run fall inference every N new frames
 
    # Spatial assignment — PPE to Person IoU threshold
    SPATIAL_IOU_THRESHOLD: float = 0.15
 

    # Alerts

    ALERT_COOLDOWN_SECONDS: int  = 10   # suppress duplicate alerts per track_id
 
 

# Singleton — import this everywhere

settings = Settings()