#!/usr/bin/env python3
"""
测试 Garmin MFA 登录流程
"""
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

from garmin.client import GarminClient

# 测试账号配置（从 test-users.json 中读取）
import json

with open("test-users.json", "r", encoding="utf-8") as f:
    config = json.load(f)

user = config["users"][0]
email = user["garmin"]["email"]
password = user["garmin"]["password"]
domain = user["garmin"].get("domain", "CN")

logger.info(f"测试账号: {email}")
logger.info(f"域名: {domain}")

# 创建客户端
client = GarminClient(
    email=email,
    password=password,
    auth_domain=domain,
    session_dir="data/.garth"
)

# 模拟 MFA 回调
def mock_mfa_callback():
    logger.info("[DEBUG] MFA 回调被调用！")
    # 这里模拟用户输入
    code = input("请输入 Garmin MFA 验证码: ")
    logger.info(f"[DEBUG] 用户输入的验证码: {code}")
    return code

# 尝试登录
logger.info("开始测试 Garmin 登录...")

try:
    result = client.login_for_ui(mock_mfa_callback)
    if result:
        logger.info("✅ 登录成功！")
    else:
        logger.error("❌ 登录失败！")
except Exception as e:
    logger.error(f"❌ 登录异常: {e}", exc_info=True)
