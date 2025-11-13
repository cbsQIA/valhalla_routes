from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    valhalla_url: str = Field(
        ..., description="Valhalla service URL", alias="VALHALLA_URL"
    )

    model_config = {"env_file": ".env", "extra": "ignore"}
