"""
GLM-4 模型相关的API端点
"""
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.glm4 import (
    GLM4Request, 
    GLM4StreamRequest, 
    GLM4APIResponse, 
    GLM4StreamAPIResponse
)
from app.services.glm4_service import glm4_service

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()


@router.post(
    "/basic",
    response_model=GLM4APIResponse,
    summary="GLM-4基础调用",
    description="调用GLM-4模型进行文本生成，返回完整响应结果"
)
async def glm4_basic_call(request: GLM4Request) -> GLM4APIResponse:
    """
    GLM-4模型基础调用接口
    
    Args:
        request: 包含prompt和temperature的请求对象
        
    Returns:
        GLM4APIResponse: 包含模型响应的API响应
        
    Raises:
        HTTPException: 当调用失败时抛出异常
    """
    try:
        logger.info(f"收到GLM-4基础调用请求，prompt长度: {len(request.prompt)}")
        
        # 调用GLM-4服务
        result = await glm4_service.basic_call(request)
        
        logger.info("GLM-4基础调用成功")
        
        return GLM4APIResponse(
            success=True,
            data=result,
            message="GLM-4调用成功"
        )
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"GLM-4基础调用失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"GLM-4基础调用失败: {str(e)}"
        )


@router.post(
    "/stream", 
    summary="GLM-4流式调用",
    description="调用GLM-4模型进行流式文本生成，实时返回生成内容"
)
async def glm4_stream_call(request: GLM4StreamRequest):
    """
    GLM-4模型流式调用接口
    
    Args:
        request: 包含prompt和temperature的流式请求对象
        
    Returns:
        StreamingResponse: 流式响应，包含实时生成的内容
        
    Raises:
        HTTPException: 当调用失败时抛出异常
    """
    try:
        logger.info(f"收到GLM-4流式调用请求，prompt长度: {len(request.prompt)}")
        
        async def generate_stream():
            """生成流式响应数据"""
            try:
                async for chunk in glm4_service.stream_call(request):
                    # 将数据格式化为SSE格式
                    chunk_data = chunk.json()
                    yield f"data: {chunk_data}\n\n"
                
                # 发送结束标志
                yield "data: [DONE]\n\n"
                logger.info("GLM-4流式调用完成")
                
            except Exception as e:
                logger.error(f"GLM-4流式调用异常: {str(e)}")
                # 发送错误信息
                error_response = GLM4StreamAPIResponse(
                    success=False,
                    data="",
                    message=f"GLM-4流式调用失败: {str(e)}",
                    error=str(e)
                )
                yield f"data: {error_response.json()}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # 禁用nginx缓冲
            }
        )
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"GLM-4流式调用失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"GLM-4流式调用失败: {str(e)}"
        )