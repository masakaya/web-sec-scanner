"""Configuration models for security scanner."""

from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ScanConfig(BaseModel):
    """Configuration for security scan.

    This model validates and stores all configuration parameters
    for running a security scan.
    """

    # Required fields
    scan_type: Literal["baseline", "full", "api", "automation"] = Field(
        ..., description="Type of scan to perform"
    )
    target_url: str = Field(..., description="Target URL to scan")

    # Authentication options
    username: Optional[str] = Field(None, description="Username for authentication")
    password: Optional[str] = Field(None, description="Password for authentication")
    auth_type: Literal["none", "form", "json", "basic"] = Field(
        "none", description="Authentication type"
    )
    login_url: Optional[str] = Field(None, description="Login endpoint URL")
    username_field: str = Field("username", description="Username field name")
    password_field: str = Field("password", description="Password field name")
    logged_in_indicator: Optional[str] = Field(
        None, description="Regex to detect logged-in state"
    )
    logged_out_indicator: Optional[str] = Field(
        None, description="Regex to detect logged-out state"
    )
    session_method: Literal["cookie", "http"] = Field(
        "cookie", description="Session management method"
    )

    # Scan options
    ajax_spider: bool = Field(
        False, description="Enable AJAX Spider for JavaScript-heavy sites"
    )
    max_duration: int = Field(30, description="Maximum scan duration in minutes", gt=0)
    max_depth: int = Field(10, description="Maximum crawl depth", gt=0)
    max_children: int = Field(20, description="Maximum children per node", gt=0)
    network_name: Optional[str] = Field(None, description="Docker network name")

    # Output directory
    report_dir: Path = Field(
        default_factory=lambda: Path.cwd() / "report",
        description="Directory to save reports",
    )

    @field_validator("target_url")
    @classmethod
    def validate_target_url(cls, v: str) -> str:
        """Validate that target_url is a valid URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("target_url must start with http:// or https://")
        return v

    @field_validator("auth_type")
    @classmethod
    def validate_auth_requirements(cls, v: str, info) -> str:
        """Validate authentication requirements.

        If auth_type is not 'none', username and password must be provided.
        """
        # Note: This validator receives the current field value (auth_type)
        # and info.data contains other fields that have been validated so far
        if v != "none":
            data = info.data
            if not data.get("username") or not data.get("password"):
                raise ValueError(
                    f"username and password are required when auth_type is '{v}'"
                )
        return v

    @field_validator("max_duration", "max_depth", "max_children")
    @classmethod
    def validate_positive(cls, v: int) -> int:
        """Validate that numeric values are positive."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v
