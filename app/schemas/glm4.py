"""
GLM-4 模型相关的数据模式
"""
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class GLM4Request(BaseModel):
    """GLM-4 基础调用请求模型"""
    prompt: str = Field(..., description="输入的提示词", min_length=1)
    temperature: Optional[float] = Field(0.7, description="生成温度", ge=0, le=2)


class GLM4StreamRequest(GLM4Request):
    """GLM-4 流式调用请求模型"""
    pass


class GLM4Choice(BaseModel):
    """GLM-4 响应选择项"""
    index: int
    message: Dict[str, Any]
    finish_reason: Optional[str] = None


class GLM4Usage(BaseModel):
    """GLM-4 使用统计"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class GLM4Response(BaseModel):
    """GLM-4 基础调用响应模型"""
    id: str
    created: int
    model: str
    request_id: str
    choices: List[GLM4Choice]
    usage: GLM4Usage


class GLM4StreamChoice(BaseModel):
    """GLM-4 流式响应选择项"""
    index: int
    delta: Dict[str, Any]
    finish_reason: Optional[str] = None


class GLM4StreamResponse(BaseModel):
    """GLM-4 流式调用响应模型"""
    id: str
    created: int
    model: str
    choices: List[GLM4StreamChoice]


class GLM4APIResponse(BaseModel):
    """统一的API响应格式"""
    success: bool = Field(default=True, description="请求是否成功")
    data: Union[GLM4Response, str] = Field(..., description="响应数据")
    message: str = Field(default="请求成功", description="响应消息")
    error: Optional[str] = Field(None, description="错误信息")


class GLM4StreamAPIResponse(BaseModel):
    """流式调用API响应格式"""
    success: bool = Field(default=True, description="请求是否成功")
    data: Union[GLM4StreamResponse, str] = Field(..., description="响应数据")
    message: str = Field(default="请求成功", description="响应消息")
    error: Optional[str] = Field(None, description="错误信息") 