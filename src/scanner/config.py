"""Configuration models for security scanner."""
# ruff: noqa: D400, D415

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from src.utils import find_project_root


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
    username: str | None = Field(None, description="Username for authentication")
    password: str | None = Field(None, description="Password for authentication")
    auth_type: Literal["none", "form", "json", "basic", "bearer"] = Field(
        "none", description="Authentication type"
    )
    login_url: str | None = Field(None, description="Login endpoint URL")
    username_field: str = Field("username", description="Username field name")
    password_field: str = Field("password", description="Password field name")
    logged_in_indicator: str | None = Field(
        None, description="Regex to detect logged-in state"
    )
    logged_out_indicator: str | None = Field(
        None, description="Regex to detect logged-out state"
    )
    session_method: Literal["cookie", "http"] = Field(
        "cookie", description="Session management method"
    )

    # Bearer/Token authentication options
    auth_token: str | None = Field(
        None, description="Bearer token for authentication (JWT, API key, etc.)"
    )
    auth_header: str = Field(
        "Authorization", description="Header name for token authentication"
    )
    token_prefix: str = Field(
        "Bearer", description="Token prefix (use 'none' for no prefix)"
    )

    # Scan options
    ajax_spider: bool = Field(
        False, description="Enable AJAX Spider for JavaScript-heavy sites"
    )
    max_duration: int = Field(30, description="Maximum scan duration in minutes", gt=0)
    max_depth: int = Field(10, description="Maximum crawl depth", gt=0)
    max_children: int = Field(20, description="Maximum children per node", gt=0)
    thread_per_host: int = Field(
        10, description="Number of threads per host for active scanning", gt=0
    )
    hosts_per_scan: int = Field(
        5, description="Number of hosts to scan in parallel", gt=0
    )
    network_name: str | None = Field(None, description="Docker network name")
    language: str = Field("ja_JP", description="Language for scanner (default: ja_JP)")
    config_file: Path | None = Field(
        None, description="Path to scan configuration preset file"
    )

    # AddOn configuration
    addons: list[str] = Field(
        default_factory=lambda: ["authhelper"],
        description="ZAP AddOns to install (e.g., authhelper, jwt, graphql, soap)",
    )

    # Output directory
    report_dir: Path = Field(
        default_factory=lambda: find_project_root() / "report",
        description="Directory to save reports",
    )

    @field_validator("target_url")
    @classmethod
    def validate_target_url(cls, v: str) -> str:
        """Validate that target_url is a valid URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("target_url must start with http:// or https://")
        return v

    @model_validator(mode="after")
    def validate_auth_requirements(self) -> "ScanConfig":
        """Validate authentication requirements.

        If auth_type is 'bearer', auth_token must be provided.
        If auth_type is not 'none' or 'bearer', username and password must be provided.
        """
        if self.auth_type == "bearer":
            if not self.auth_token:
                raise ValueError("auth_token is required when auth_type is 'bearer'")
        elif self.auth_type != "none" and (not self.username or not self.password):
            raise ValueError(
                f"username and password are required when auth_type is '{self.auth_type}'"
            )
        return self

    @field_validator(
        "max_duration", "max_depth", "max_children", "thread_per_host", "hosts_per_scan"
    )
    @classmethod
    def validate_positive(cls, v: int) -> int:
        """Validate that numeric values are positive."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v
