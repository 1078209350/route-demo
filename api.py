#!/usr/bin/env python3
"""
FastAPI 接口服务
"""

import sys
import os

# 将父目录添加到 sys.path，以便导入 router 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from core.classifier import Classifier

app = FastAPI(title="问题分类API", version="1.0.0")

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

classifier = Classifier()


@app.get("/")
def root():
    return {"message": "问题分类API", "version": "1.0.0"}


@app.post("/classify")
async def classify(request: Request):
    """
    分类接口 - 取 messages[0].content 当作 question
    """
    try:
        # 尝试解析 JSON body
        body = await request.json()
    except:
        # 如果不是 JSON，尝试 FormData
        form_data = await request.form()
        if "messages" in form_data:
            body = {"messages": json.loads(form_data["messages"])}
        elif "question" in form_data:
            body = {"question": form_data["question"]}
        else:
            return {"success": False, "error": "invalid request format"}

    # 取 messages 第一条的 content
    question = None
    messages = body.get("messages", [])
    if messages and len(messages) > 0:
        question = messages[0].get("content")

    # 如果没有 messages，取 question 字段
    if not question:
        question = body.get("question")

    if not question:
        return {"success": False, "error": "question is required"}

    result = classifier.classify(question)

    return {
        "success": True,
        "question": question,
        "category": result.value if result else "OTHER"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
