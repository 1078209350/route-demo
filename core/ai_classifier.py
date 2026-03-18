import yaml
import hashlib
import time
import os
from typing import Optional, Dict, Any
from pathlib import Path
from collections import OrderedDict

from models.category import Category
from utils.logger import get_logger


logger = get_logger(__name__)


class LRUCache:
    """简单LRU缓存"""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl

    def get(self, key: str) -> Optional[str]:
        if key not in self.cache:
            return None

        # 检查是否过期
        timestamp, value = self.cache[key]
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return None

        # 移到末尾
        self.cache.move_to_end(key)
        return value

    def set(self, key: str, value: str):
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
        self.cache[key] = (time.time(), value)

    def clear(self):
        self.cache.clear()


class AIClassifier:
    """AI意图识别分类器"""

    CATEGORY_PROMPT = """你是一个问题分类助手。请根据以下问题判断它属于哪个类别。

类别定义：
- 工具类: 锤子、螺丝刀、扳手、钳子、锯子等手动或电动工具
- 容器类: 盒子、箱子、瓶子、罐子、桶等用于盛装物品的容器
- 装饰品类: 花、植物、盆栽、画、雕像、灯具、地毯等装饰用品
- 消耗品类: 纸、笔、墨水、电池、燃料、胶水等一次性或需补充的物品
- 交通工具类: 汽车、自行车、摩托车、飞机、火车、船等交通工具
- 其他类: 不属于上述类别的物品

问题: {question}

请直接返回类别名称，不要包含其他内容。"""

    def __init__(self, config_path: Optional[str] = None):
        self.enabled = False
        self.provider = "claude"
        self.model = "claude-sonnet-4-20250514"
        self.endpoint = None  # 自定义 API 端点
        self.api_key = None   # API Key
        self.max_retries = 2
        self.timeout = 30
        self.cache_enabled = True
        self.cache = LRUCache(max_size=1000, ttl=3600)

        self._load_config(config_path)

    def _load_config(self, config_path: Optional[str]):
        """加载AI配置"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "rules.yaml"
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            logger.warning(f"AI config not found: {config_path}")
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            ai_config = config.get("ai", {})
            self.enabled = ai_config.get("enabled", False)
            self.provider = ai_config.get("provider", "claude")
            self.model = ai_config.get("model", "claude-sonnet-4-20250514")
            self.endpoint = ai_config.get("endpoint", None)
            self.api_key = ai_config.get("api_key", None)
            self.max_retries = ai_config.get("max_retries", 2)
            self.timeout = ai_config.get("timeout", 30)

            cache_config = config.get("cache", {})
            self.cache_enabled = cache_config.get("enabled", True)
            self.cache = LRUCache(
                max_size=cache_config.get("max_size", 1000),
                ttl=cache_config.get("ttl", 3600)
            )

            logger.info(f"AI classifier loaded, enabled: {self.enabled}, provider: {self.provider}")

        except Exception as e:
            logger.error(f"Failed to load AI config: {e}")

    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def _call_ai(self, text: str) -> Optional[str]:
        """调用AI API"""
        prompt = self.CATEGORY_PROMPT.format(question=text)

        try:
            if self.provider == "claude":
                return self._call_claude(prompt)
            elif self.provider == "openai":
                return self._call_openai(prompt)
            elif self.provider == "minimax":
                return self._call_minimax(prompt)
            else:
                logger.error(f"Unknown provider: {self.provider}")
                return None
        except Exception as e:
            logger.error(f"AI call failed: {e}")
            return None

    def _call_claude(self, prompt: str) -> Optional[str]:
        """调用Claude API"""
        try:
            import anthropic
            client = anthropic.Anthropic()
            response = client.messages.create(
                model=self.model,
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}]
            )
            # 处理新版 anthropic SDK 响应结构
            for block in response.content:
                if hasattr(block, 'type') and block.type == 'text':
                    return block.text.strip()
                # 兼容旧版
                elif hasattr(block, 'text'):
                    return block.text.strip()
            return None
        except ImportError:
            logger.error("anthropic package not installed")
            return None
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            return None

    def _call_openai(self, prompt: str) -> Optional[str]:
        """调用OpenAI API"""
        try:
            import openai
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50
            )
            return response.choices[0].message.content.strip()
        except ImportError:
            logger.error("openai package not installed")
            return None
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return None

    def _call_minimax(self, prompt: str) -> Optional[str]:
        """调用MiniMax API (官方推荐方式: OpenAI兼容客户端)"""
        try:
            import openai

            # 优先使用配置文件中的 api_key，否则使用环境变量
            api_key = self.api_key or os.environ.get("MINIMAX_API_KEY")
            if not api_key:
                logger.error("MINIMAX_API_KEY not set in config or environment")
                return None

            # 确保 base_url 包含 /v1
            base_url = self.endpoint or "https://api.minimax.chat"
            if not base_url.endswith("/v1"):
                base_url = base_url.rstrip("/") + "/v1"

            client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url
            )

            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50
            )
            return response.choices[0].message.content.strip()
        except ImportError:
            logger.error("openai package not installed")
            return None
        except Exception as e:
            logger.error(f"MiniMax API call failed: {e}")
            return None

    def classify(self, text: str) -> Optional[Category]:
        """
        使用AI对文本进行分类

        Args:
            text: 待分类文本

        Returns:
            分类结果，未成功返回None
        """
        if not self.enabled:
            logger.debug("AI classifier is disabled")
            return None

        if not text:
            return None

        # 尝试从缓存获取
        if self.cache_enabled:
            cache_key = self._get_cache_key(text)
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for: {text[:30]}")
                return Category.from_string(cached_result)

        # 调用AI
        result = self._call_ai(text)
        if result:
            category = Category.from_string(result)
            if category != Category.OTHER:
                # 缓存结果
                if self.cache_enabled:
                    self.cache.set(cache_key, category.value)
                logger.info(f"AI classified: '{text[:30]}' -> {category.value}")
                return category

        return None
