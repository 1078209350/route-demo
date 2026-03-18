#!/usr/bin/env python3
"""
问题分类系统入口
"""

import sys
import os

# 将父目录添加到 sys.path，以便导入 router 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from core.classifier import Classifier
from models.category import Category


def main():
    """测试分类器"""
    classifier = Classifier()

    # 测试问题
    test_questions = [
        "我的锤子坏了，怎么修？",
        "这个盒子用什么材料做的？",
        "你知道火车吗",
        "你能做什么！"
    ]

    print("=" * 50)
    print("问题分类系统测试")
    print("=" * 50)

    # 问题1: 返回"其他类"
    question = test_questions[0]
    result = classifier.classify(question)
    print(f"问题: {question}")
    print(f"分类: {result.value}")
    print("-" * 50)

    # 问题2: JSON格式返回
    question = test_questions[1]
    result = classifier.classify(question)
    output = {
        "question": question,
        "category": result.value,
        "category_code": result.name
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    print("-" * 50)

    # 问题3: 测试"火车"
    question = test_questions[2]
    result = classifier.classify(question)
    print(f"问题: {question}")
    print(f"分类: {result.value}")
    print("-" * 50)

    # 问题4: 测试"其他类"
    question = test_questions[3]
    result = classifier.classify(question)
    print(f"问题: {question}")
    print(f"分类: {result.value}")
    print("-" * 50)



if __name__ == "__main__":
    main()
