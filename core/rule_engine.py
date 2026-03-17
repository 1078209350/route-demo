import re
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path

from router.models.category import Category
from router.utils.logger import get_logger


logger = get_logger(__name__)


class RuleMatcher:
    """规则匹配器基类"""

    def match(self, text: str, config: Dict[str, Any]) -> bool:
        raise NotImplementedError


class KeywordMatcher(RuleMatcher):
    """关键词匹配器 - 完全包含"""

    def match(self, text: str, config: Dict[str, Any]) -> bool:
        values = config.get("values", [])
        logic = config.get("logic", "any")

        if not values:
            return False

        text = text.lower()
        matches = [v.lower() in text for v in values]

        if logic == "all":
            return all(matches)
        return any(matches)


class PrefixMatcher(RuleMatcher):
    """前缀匹配器 - 以指定前缀开头"""

    def match(self, text: str, config: Dict[str, Any]) -> bool:
        values = config.get("values", [])
        logic = config.get("logic", "any")

        if not values:
            return False

        matches = [text.startswith(v) for v in values]

        if logic == "all":
            return all(matches)
        return any(matches)


class RegexMatcher(RuleMatcher):
    """正则表达式匹配器"""

    def match(self, text: str, config: Dict[str, Any]) -> bool:
        pattern = config.get("pattern")
        if not pattern:
            return False

        try:
            return bool(re.search(pattern, text))
        except re.error as e:
            logger.error(f"Invalid regex pattern: {pattern}, error: {e}")
            return False


class Rule:
    """规则定义"""

    MATCHER_MAP = {
        "keyword": KeywordMatcher,
        "prefix": PrefixMatcher,
        "regex": RegexMatcher,
    }

    def __init__(self, category: Category, name: str, priority: int, matchers: List[Dict[str, Any]]):
        self.category = category
        self.name = name
        self.priority = priority
        self.matchers_config = matchers
        self.matchers: List[RuleMatcher] = []
        self._matcher_instances = {}  # 存储 matcher 实例到配置的映射

        self._init_matchers()

    def _init_matchers(self):
        """初始化匹配器"""
        for config in self.matchers_config:
            matcher_type = config.get("type")
            if matcher_type in self.MATCHER_MAP:
                matcher_instance = self.MATCHER_MAP[matcher_type]()
                self.matchers.append(matcher_instance)
                self._matcher_instances[id(matcher_instance)] = config

    def match(self, text: str) -> bool:
        """检查文本是否匹配此规则"""
        if not self.matchers:
            return False

        # 所有匹配器都需匹配成功 (and 逻辑)
        for matcher in self.matchers:
            config = self._matcher_instances.get(id(matcher), {})
            if not matcher.match(text, config):
                return False
        return True

    def _get_matcher_config(self, matcher: RuleMatcher) -> Dict[str, Any]:
        """获取匹配器配置"""
        return self._matcher_instances.get(id(matcher), {})


class RuleEngine:
    """规则引擎"""

    def __init__(self, config_path: Optional[str] = None):
        self.rules: List[Rule] = []
        self.default_category = Category.OTHER
        self.config_path = config_path
        self._load_rules()

    def _load_rules(self):
        """加载规则配置"""
        if self.config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "rules.yaml"
        else:
            config_path = Path(self.config_path)

        if not config_path.exists():
            logger.warning(f"Rules config not found: {config_path}")
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            rules_config = config.get("rules", [])
            for rule_config in rules_config:
                category = Category.from_string(rule_config.get("category", "OTHER"))
                name = rule_config.get("name", "")
                priority = rule_config.get("priority", 0)
                matchers = rule_config.get("matchers", [])

                rule = Rule(category, name, priority, matchers)
                self.rules.append(rule)

            # 按优先级排序
            self.rules.sort(key=lambda r: r.priority, reverse=True)

            # 设置默认分类
            default = config.get("default_category", "OTHER")
            self.default_category = Category.from_string(default)

            logger.info(f"Loaded {len(self.rules)} rules")

        except Exception as e:
            logger.error(f"Failed to load rules: {e}")

    def classify(self, text: str) -> Optional[Category]:
        """
        对文本进行分类

        Args:
            text: 待分类文本

        Returns:
            匹配的分类，未匹配返回None
        """
        if not text:
            return None

        for rule in self.rules:
            if rule.match(text):
                logger.info(f"Rule '{rule.name}' matched for text: {text[:50]}")
                return rule.category

        logger.info(f"No rule matched for text: {text[:50]}")
        return None

    def reload(self):
        """重新加载规则"""
        self.rules = []
        self._load_rules()
