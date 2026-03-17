import logging
from enum import Enum


class Category(Enum):
    """问题分类枚举"""
    TOOL = "工具类"          # 工具类
    CONTAINER = "容器类"      # 容器类
    DECORATION = "装饰品类"   # 装饰品类
    CONSUMABLE = "消耗品类"   # 消耗品类
    VEHICLE = "交通工具类"    # 交通工具类
    OTHER = "其他类"          # 其他类

    @classmethod
    def default(cls) -> "Category":
        """返回默认分类"""
        return cls.OTHER

    @classmethod
    def from_string(cls, value: str) -> "Category":
        """从字符串转换为枚举"""
        value = value.strip()
        for category in cls:
            if category.value == value or category.name == value.upper():
                return category
        return cls.DEFAULT
