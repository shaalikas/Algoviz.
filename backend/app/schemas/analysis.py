from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from urllib.parse import urlsplit


class AnalysisOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    include_external_dependencies: bool = True
    detect_risks: bool = True
    generate_ai_summary: bool = True


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    repository_url: str = Field(min_length=1, max_length=2048)
    options: AnalysisOptions = Field(default_factory=AnalysisOptions)

    @field_validator("repository_url")
    @classmethod
    def github_repository_url(cls, value: str) -> str:
        value = value.strip()
        parsed = urlsplit(value)
        parts = [part for part in parsed.path.strip("/").split("/") if part]
        if (parsed.scheme != "https" or parsed.hostname != "github.com" or
                parsed.username or parsed.password or len(parts) != 2 or
                any(part in {".", ".."} for part in parts)):
            raise ValueError("Enter a GitHub repository URL, such as https://github.com/owner/repository.")
        return f"https://github.com/{parts[0]}/{parts[1].removesuffix('.git')}"


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    success: bool = True
    analysis_id: str
    repository: dict[str, Any] = Field(default_factory=dict)
    architecture: dict[str, Any] = Field(default_factory=dict)
    diagrams: dict[str, Any] = Field(default_factory=dict)
    file_tree: Any = Field(default_factory=dict)
    insights: dict[str, Any] = Field(default_factory=dict)
    risks: Any = Field(default_factory=dict)


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorBody
