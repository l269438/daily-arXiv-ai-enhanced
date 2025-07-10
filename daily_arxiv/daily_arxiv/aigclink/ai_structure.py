#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AIGCLINK AI结构模型 - 用于提取产品的专利点和创新点
"""

from pydantic import BaseModel, Field
from typing import List

class AIGCLINKAnalysis(BaseModel):
    """AIGCLINK产品分析结构"""
    summary: str = Field(description="产品的简短摘要，概述其主要功能和用途")
    key_features: str = Field(description="产品的关键特性，用逗号分隔")
    innovation_points: str = Field(description="产品的创新点分析")
    patent_ideas: str = Field(description="从产品描述中提取的可能的专利点")
    use_cases: str = Field(description="产品的主要应用场景")
    tech_stack: str = Field(description="推测的产品技术栈")
    market_potential: str = Field(description="产品的市场潜力分析")
    improvement_suggestions: str = Field(description="对产品的改进建议")