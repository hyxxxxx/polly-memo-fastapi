"""
GLM-4 模型调用服务
"""
import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, Union, Optional
import httpx
from fastapi import HTTPException
from app.core.config import settings
from app.schemas.glm4 import GLM4Request, GLM4Response, GLM4StreamRequest, GLM4StreamResponse

# 配置日志
logger = logging.getLogger(__name__)


class GLM4Service:
    """GLM-4 模型调用服务"""
    
    def __init__(self):
        """初始化服务"""
        self.api_key = settings.glm4_api_key
        self.base_url = settings.glm4_base_url
        self.model = settings.glm4_model
        self.timeout = settings.glm4_timeout
        self.max_tokens = settings.glm4_max_tokens
        
        # 设置请求头
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _build_messages(self, prompt: str) -> list:
        """构建消息格式"""
        return [
            {
                "role": "user",
                "content": prompt
            }
        ]
    
    def _build_request_payload(self, prompt: str, temperature: Optional[float], stream: bool = False) -> Dict[str, Any]:
        """构建请求载荷"""
        payload = {
            "model": self.model,
            "messages": self._build_messages(prompt),
            "temperature": temperature if temperature is not None else 0.7,
            "max_tokens": self.max_tokens
        }
        
        if stream:
            payload["stream"] = True
            
        return payload
    
    async def basic_call(self, request: GLM4Request) -> GLM4Response:
        """
        基础调用GLM-4模型
        
        Args:
            request: GLM-4请求对象
            
        Returns:
            GLM4Response: 模型响应结果
            
        Raises:
            HTTPException: 当API调用失败时
        """
        try:
            # 构建请求载荷
            payload = self._build_request_payload(
                prompt=request.prompt,
                temperature=request.temperature,
                stream=False
            )
            
            # 发送HTTP请求
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                
                # 检查响应状态
                if response.status_code != 200:
                    logger.error(f"GLM-4 API调用失败: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"GLM-4 API调用失败: {response.text}"
                    )
                
                # 解析响应
                result = response.json()
                logger.info(f"GLM-4 基础调用成功，模型：{result.get('model')}")
                
                return GLM4Response(**result)
                
        except httpx.TimeoutException:
            logger.error("GLM-4 API调用超时")
            raise HTTPException(status_code=408, detail="GLM-4 API调用超时")
        except httpx.RequestError as e:
            logger.error(f"GLM-4 API请求错误: {str(e)}")
            raise HTTPException(status_code=500, detail=f"GLM-4 API请求错误: {str(e)}")
        except Exception as e:
            logger.error(f"GLM-4 基础调用异常: {str(e)}")
            raise HTTPException(status_code=500, detail=f"GLM-4 调用失败: {str(e)}")
    
    async def stream_call(self, request: GLM4StreamRequest) -> AsyncGenerator[GLM4StreamResponse, None]:
        """
        流式调用GLM-4模型
        
        Args:
            request: GLM-4流式请求对象
            
        Yields:
            GLM4StreamResponse: 流式响应数据块
            
        Raises:
            HTTPException: 当API调用失败时
        """
        try:
            # 构建请求载荷
            payload = self._build_request_payload(
                prompt=request.prompt,
                temperature=request.temperature,
                stream=True
            )
            
            # 发送流式HTTP请求
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                ) as response:
                    
                    # 检查响应状态
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"GLM-4 流式API调用失败: {response.status_code} - {error_text.decode()}")
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"GLM-4 流式API调用失败: {error_text.decode()}"
                        )
                    
                    logger.info("GLM-4 流式调用开始")
                    
                    # 逐行读取流式响应
                    async for line in response.aiter_lines():
                        if line.strip():
                            # 处理SSE格式的数据
                            if line.startswith("data: "):
                                data_str = line[6:].strip()  # 去掉 "data: " 前缀
                                
                                # 检查结束标志
                                if data_str == "[DONE]":
                                    logger.info("GLM-4 流式调用完成")
                                    break
                                
                                try:
                                    # 解析JSON数据
                                    data = json.loads(data_str)
                                    yield GLM4StreamResponse(**data)
                                except json.JSONDecodeError as je:
                                    logger.warning(f"解析流式响应JSON失败: {je}")
                                    continue
                                except Exception as pe:
                                    logger.warning(f"解析流式响应失败: {pe}")
                                    continue
                    
        except httpx.TimeoutException:
            logger.error("GLM-4 流式API调用超时")
            raise HTTPException(status_code=408, detail="GLM-4 流式API调用超时")
        except httpx.RequestError as e:
            logger.error(f"GLM-4 流式API请求错误: {str(e)}")
            raise HTTPException(status_code=500, detail=f"GLM-4 流式API请求错误: {str(e)}")
        except Exception as e:
            logger.error(f"GLM-4 流式调用异常: {str(e)}")
            raise HTTPException(status_code=500, detail=f"GLM-4 流式调用失败: {str(e)}")


# 全局服务实例
glm4_service = GLM4Service() 