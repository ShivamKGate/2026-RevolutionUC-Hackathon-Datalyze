from pydantic import BaseModel


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    setup_complete: bool
    onboarding_path: str | None = None


class SetupRequest(BaseModel):
    company_name: str
    display_name: str | None = None
    job_title: str | None = None
    onboarding_path: str  # devops | automations | deep_analysis
