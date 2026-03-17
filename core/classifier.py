from typing import Optional
from pathlib import Path

from router.models.category import Category
from router.core.rule_engine import RuleEngine
from router.core.ai_classifier import AIClassifier
from router.utils.logger import get_logger


logger = get_logger(__name__)


class Classifier:
    """
    两阶段问题分类器

    流程: 规则匹配 -> AI识别 -> 返回默认值
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化分类器

        Args:
            config_path: 规则配置文件路径
        """
        self.rule_engine = RuleEngine(config_path)
        self.ai_classifier = AIClassifier(config_path)

        logger.info("Classifier initialized")

    def classify(self, text: str) -> Category:
        """
        对问题进行分类

        Args:
            text: 用户问题

        Returns:
            分类结果
        """
        if not text:
            logger.warning("Empty text provided, returning default category")
            return Category.default()

        text = text.strip()

        # 阶段1: 规则匹配
        logger.info(f"Stage 1 - Rule matching for: {text[:50]}")
        category = self.rule_engine.classify(text)
        if category:
            logger.info(f"Rule matched: {category.value}")
            return category

        # 阶段2: AI识别
        logger.info(f"Stage 2 - AI classification for: {text[:50]}")
        category = self.ai_classifier.classify(text)
        if category:
            logger.info(f"AI classified: {category.value}")
            return category

        # 返回默认值
        logger.info(f"Using default category")
        return Category.default()

    def reload_rules(self):
        """重新加载规则"""
        self.rule_engine.reload()
        logger.info("Rules reloaded")

    def clear_cache(self):
        """清空AI缓存"""
        self.ai_classifier.cache.clear()
        logger.info("AI cache cleared")
