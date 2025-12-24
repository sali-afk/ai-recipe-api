"""
通义千问视觉API客户端 (OpenAI-compatible)
使用 qwen-vl-plus 模型一步到位，从图片直接生成结构化的菜谱JSON
"""
import os
import logging
import base64
import json

from openai import OpenAI
from pydantic import ValidationError

from app.models.schemas import Recipe


logger = logging.getLogger(__name__)


class QwenVisionClient:
    """
    通义千问视觉API客户端 (OpenAI-compatible)
    """

    def __init__(self):
        self.api_key: str = os.getenv("DASHSCOPE_API_KEY") or ""
        if not self.api_key:
            logger.error("CRITICAL: DASHSCOPE_API_KEY 环境变量未设置!")
            raise ValueError("DASHSCOPE_API_KEY 环境变量未设置!")

        try:
            self.client: OpenAI = OpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
            logger.info("QwenVisionClient (OpenAI-compatible) 初始化成功。")
        except Exception as e:
            logger.error(f"OpenAI 客户端初始化失败: {e}", exc_info=True)
            raise

    async def generate_recipe_from_image(self, image_bytes: bytes) -> Recipe:
        """
        接收图片，调用qwen3-vl-plus模型，返回结构化的菜谱对象
        """
        if not image_bytes:
            raise ValueError("图片数据不能为空")

        logger.info("使用 qwen3-vl-plus 模型生成完整菜谱...")
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        image_url = f"data:image/jpeg;base64,{base64_image}"

        prompt = """你是一位经验丰富的美食家和厨师。请根据这张图片，完成以下任务：
1. 识别图片中的主要食材。
2. 围绕这些食材，构思一道美味、有创意的菜肴。
3. 以严格的JSON格式返回这道菜的菜谱。JSON对象必须包含以下字段：
   - "dish_name": "菜品名称" (字符串)
   - "ingredients": [{"name": "食材名", "amount": "用量", "unit": "单位"}, ...] (对象数组)
   - "steps": [{"step_number": 1, "description": "步骤描述", "duration": 分钟数}, ...] (对象数组)
   - "cooking_time": 总烹饪时间 (整数, 分钟)
   - "difficulty": "难度" (字符串, 例如：简单, 中等, 困难)

请确保返回的只有纯粹的、不含任何额外解释和Markdown标记的JSON字符串。
"""

        response_content: str = ""
        try:
            completion = self.client.chat.completions.create(
                model="qwen3-vl-plus",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                },
                            },
                        ],
                    },
                ],
            )

            response_content = completion.choices[0].message.content or ""
            if not response_content.strip():
                raise ValueError("模型未返回有效文本内容")

            logger.info(f"API 成功响应，内容长度: {len(response_content)}")

            recipe_data = json.loads(response_content)

            # 使用Pydantic模型进行验证和转换，确保数据结构正确
            recipe = Recipe.model_validate(recipe_data)

            logger.info(f"成功生成并解析菜谱: {recipe.dish_name}")
            return recipe

        except json.JSONDecodeError as e:
            logger.error(f"解析AI返回的JSON时失败: {e}", exc_info=True)
            logger.error(f"错误的JSON内容: {response_content}")
            raise ValueError("AI模型返回的菜谱格式无效，无法解析。")
        except ValidationError as e:
            logger.error(f"AI返回的JSON结构不符合预期的菜谱格式: {e}", exc_info=True)
            raise ValueError("AI模型返回的数据结构不正确。")
        except Exception as e:
            logger.error(f"调用通义千问API或解析响应时出错: {e}", exc_info=True)
            raise

    async def close(self):
        logger.info("QwenVisionClient closed.")
        pass

