from pydantic import BaseModel, Field


class BugReport(BaseModel):
    title: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    expected_behavior: str = Field(min_length=1)
    actual_behavior: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
