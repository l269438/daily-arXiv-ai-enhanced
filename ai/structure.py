from pydantic import BaseModel, Field
from typing import List

class Structure(BaseModel):
  tldr: str = Field(description="generate a too long; didn't read summary")
  motivation: str = Field(description="describe the motivation in this paper")
  method: str = Field(description="method of this paper")
  result: str = Field(description="result of this paper")
  conclusion: str = Field(description="conclusion of this paper")
  idea_en: List[str] = Field(description="extract innovative patent ideas from this paper in English, return as a list")
  idea_ch: List[str] = Field(description="extract innovative patent ideas from this paper in Chinese, return as a list")