from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: bool = False


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    setup_complete: bool
    onboarding_path: str | None = None
    display_name: str | None = None
    job_title: str | None = None
    company_id: int | None = None
    company_name: str | None = None
    public_scrape_enabled: bool = False


class ProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    job_title: str | None = Field(default=None, max_length=100)


class CompanyUpdateRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    public_scrape_enabled: bool | None = None
    onboarding_path: str | None = Field(default=None, max_length=120)


class PreferencesUpdateRequest(BaseModel):
    """User-scoped settings (not shared across the company workspace)."""

    onboarding_path: str = Field(min_length=1, max_length=120)


class SetupRequest(BaseModel):
    company_name: str
    display_name: str | None = None
    job_title: str | None = None
    onboarding_path: str  # devops | automations | deep_analysis
