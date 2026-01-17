"""
同步服务编排器
提供统一的同步接口，供 GUI 和 CLI 调用
"""
import logging
import datetime
from typing import Generator, Optional, List, Dict, Any
from pathlib import Path

from .models import SyncProgress, SyncResult, UserModel
from .config_manager import EnhancedConfigManager

logger = logging.getLogger(__name__)

# Import existing modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from xiaomi.client import XiaomiClient, unmarshal_fitness_data
from garmin.client import GarminClient
from garmin.fit_generator import create_weight_fit_file
from utils.paths import get_session_dir, get_output_dir


class SyncOrchestrator:
    """同步编排器 - 协调整个同步流程"""

    def __init__(self, config_path: str = "users.json"):
        """
        初始化同步编排器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config_mgr = EnhancedConfigManager(config_path)
        self._should_stop = False

    def reload_config(self, new_config_path: str):
        """
        重新加载配置文件

        Args:
            new_config_path: 新的配置文件路径
        """
        self.config_path = new_config_path
        self.config_mgr = EnhancedConfigManager(new_config_path)
        logger.info(f"配置文件已重新加载：{new_config_path}")

    def list_users(self) -> List[UserModel]:
        """获取所有用户列表"""
        return self.config_mgr.get_users()

    def get_user(self, username: str) -> Optional[UserModel]:
        """获取指定用户"""
        return self.config_mgr.get_user(username)

    def save_user(self, user: UserModel) -> bool:
        """保存用户（添加或更新）"""
        return self.config_mgr.add_or_update_user(user)

    def delete_user(self, username: str) -> bool:
        """删除用户"""
        return self.config_mgr.delete_user(username)

    def sync_user(
        self,
        username: str,
        chunk_size: int = 500,
        input_callback=None
    ) -> Generator[SyncProgress, None, None]:
        """
        执行同步，返回进度生成器

        Args:
            username: 用户名
            chunk_size: 分块大小（默认 500）
            input_callback: 用户输入回调函数（用于登录时需要用户输入）

        Yields:
            SyncProgress: 同步进度信息
        """
        try:
            self._should_stop = False

            # 获取用户配置
            user = self.get_user(username)
            if not user:
                yield SyncProgress(
                    stage="error",
                    current=0,
                    total=100,
                    message=f"❌ 用户不存在: {username}",
                    timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                    username=username
                )
                return

            # 阶段 1: 登录小米并获取数据
            yield SyncProgress(
                stage="fetching",
                current=10,
                total=100,
                message="📱 正在登录小米...",
                timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                username=username
            )

            xiaomi_client = XiaomiClient(username=user.username)

            # 检查是否有可用 token
            has_valid_token = (
                user.token and
                user.token.userId and
                user.token.passToken
            )

            if not has_valid_token:
                # 尝试用户名密码登录
                yield SyncProgress(
                    stage="fetching",
                    current=15,
                    total=100,
                    message="🔐 需要登录小米账号...",
                    timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                    username=username
                )

                # 通过回调请求 GUI 弹出登录对话框
                if not input_callback:
                    yield SyncProgress(
                        stage="error",
                        current=0,
                        total=100,
                        message="❌ 未配置小米 Token 且无法进行交互式登录",
                        timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                        username=username
                    )
                    return

                login_result = input_callback({
                    "action": "xiaomi_login",
                    "username": user.username,
                    "password": user.password if user.password else None
                })

                if not login_result.get("success"):
                    error_msg = login_result.get("error", "未知错误")
                    yield SyncProgress(
                        stage="error",
                        current=0,
                        total=100,
                        message=f"❌ 小米登录失败: {error_msg}",
                        timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                        username=username
                    )
                    return

                # 保存 token
                token_data = login_result["token"]
                self.config_mgr.update_user_token(username, token_data)
                logger.info(f"用户 {username} 登录成功,Token 已保存")

                # 设置凭证到 client
                xiaomi_client.set_credentials(
                    user_id=token_data["userId"],
                    ssecurity_encoded=token_data["ssecurity"],
                    pass_token=token_data["passToken"]
                )

                # 刷新 token
                try:
                    new_token_data = xiaomi_client.login_from_token()
                    if new_token_data:
                        self.config_mgr.update_user_token(username, new_token_data)
                        logger.info(f"用户 {username} 的 Token 已刷新")
                except Exception as e:
                    # Token 刷新失败,但继续使用刚获取的 token
                    logger.warning(f"Token 刷新失败,但继续使用: {e}")

            else:
                # 使用现有 token
                xiaomi_client.set_credentials(
                    user_id=user.token.userId,
                    ssecurity_encoded=user.token.ssecurity,
                    pass_token=user.token.passToken
                )

                try:
                    # 刷新 Token
                    yield SyncProgress(
                        stage="fetching",
                        current=20,
                        total=100,
                        message="🔄 正在刷新小米 Token...",
                        timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                        username=username
                    )

                    new_token_data = xiaomi_client.login_from_token()
                    if new_token_data:
                        self.config_mgr.update_user_token(username, new_token_data)
                        logger.info(f"用户 {username} 的 Token 已刷新")

                except Exception as e:
                    yield SyncProgress(
                        stage="error",
                        current=0,
                        total=100,
                        message=f"❌ 小米登录失败: {str(e)}",
                        timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                        username=username
                    )
                    return

            # 获取体重数据
            yield SyncProgress(
                stage="fetching",
                current=30,
                total=100,
                message="📊 正在获取体重数据...",
                timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                username=username
            )

            weights = []
            try:
                # 尝试新 API
                weights = xiaomi_client.get_model_weights(user.model)

                if not weights:
                    # 回退到旧 API
                    fitness_data = xiaomi_client.get_fitness_data_by_time(key="weight")
                    weights = unmarshal_fitness_data(fitness_data)

                if not weights:
                    yield SyncProgress(
                        stage="error",
                        current=0,
                        total=100,
                        message="❌ 未获取到任何体重数据",
                        timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                        username=username
                    )
                    return

            except Exception as e:
                yield SyncProgress(
                    stage="error",
                    current=0,
                    total=100,
                    message=f"❌ 获取体重数据失败: {str(e)}",
                    timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                    username=username
                )
                return

            yield SyncProgress(
                stage="fetching",
                current=40,
                total=100,
                message=f"✅ 成功获取 {len(weights)} 条体重数据",
                timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                username=username,
                details={"total_weights": len(weights)}
            )

            # 检查是否有 Garmin 配置
            if not user.garmin or not user.garmin.email:
                yield SyncProgress(
                    stage="error",
                    current=0,
                    total=100,
                    message="❌ 未配置 Garmin 账号信息",
                    timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                    username=username
                )
                return

            # 阶段 2: 生成 FIT 文件并分块
            yield SyncProgress(
                stage="generating",
                current=50,
                total=100,
                message="📝 正在生成 FIT 文件...",
                timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                username=username
            )

            # 分块处理
            weight_chunks = [weights[i:i+chunk_size]
                            for i in range(0, len(weights), chunk_size)]
            total_chunks = len(weight_chunks)

            yield SyncProgress(
                stage="generating",
                current=55,
                total=100,
                message=f"📦 数据将分为 {total_chunks} 个批次处理",
                timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                username=username,
                details={"total_chunks": total_chunks}
            )

            # 创建输出目录（使用可写路径）
            output_dir = get_output_dir(
                custom_base=getattr(self.config_mgr, 'custom_data_dir', None)
            )
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

            # 阶段 3: 登录 Garmin
            yield SyncProgress(
                stage="uploading",
                current=60,
                total=100,
                message="🏃 正在登录 Garmin...",
                timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                username=username
            )

            # 获取可写的会话目录（修复打包后的只读文件系统问题）
            session_dir = get_session_dir(
                email=user.garmin.email,
                custom_base=getattr(self.config_mgr, 'custom_data_dir', None)
            )

            garmin_client = GarminClient(
                email=user.garmin.email,
                password=user.garmin.password,
                auth_domain=user.garmin.domain,
                session_dir=str(session_dir)  # 关键：传入可写路径
            )

            # 登录 Garmin - 根据是否有 input_callback 选择登录方法
            if input_callback:
                # UI 模式：使用 login_for_ui，支持 MFA 对话框
                yield SyncProgress(
                    stage="uploading",
                    current=60,
                    total=100,
                    message="🏃 正在登录 Garmin（如启用了两步验证，请输入验证码）...",
                    timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                    username=username
                )

                # 通过 input_callback 获取 MFA 验证码
                def get_mfa_code():
                    logger.info(f"[DEBUG] get_mfa_code 被调用，正在请求用户输入...")
                    mfa_result = input_callback({
                        "action": "garmin_mfa",
                        "username": username,
                        "email": user.garmin.email
                    })
                    logger.info(f"[DEBUG] 收到 MFA 结果: {mfa_result}")
                    return mfa_result.get("mfa_code", "")

                login_success = garmin_client.login_for_ui(get_mfa_code)
            else:
                # CLI 模式：使用原有 login 方法
                login_success = garmin_client.login()

            if not login_success:
                yield SyncProgress(
                    stage="error",
                    current=0,
                    total=100,
                    message="❌ Garmin 登录失败",
                    timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                    username=username
                )
                return

            # 上传结果统计
            upload_results = {
                'success': 0,
                'failed': 0,
                'duplicate': 0,
                'failed_chunks': []
            }

            # 阶段 4: 逐个处理和上传
            for idx, chunk in enumerate(weight_chunks, 1):
                if self._should_stop:
                    yield SyncProgress(
                        stage="stopped",
                        current=0,
                        total=100,
                        message="⏸️ 同步已停止",
                        timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                        username=username
                    )
                    return

                chunk_filename = output_dir / f"weight_{username}_{timestamp}_{idx}.fit"

                yield SyncProgress(
                    stage="generating",
                    current=60 + (idx * 30 // total_chunks),
                    total=100,
                    message=f"📝 生成 FIT 文件: 批次 {idx}/{total_chunks}",
                    timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                    username=username,
                    details={
                        "chunk": idx,
                        "total_chunks": total_chunks,
                        "records": len(chunk),
                        "filename": str(chunk_filename)
                    }
                )

                # 生成 FIT 文件
                filter_config = user.garmin.filter if user.garmin else None
                created_path = create_weight_fit_file(
                    chunk,
                    chunk_filename,
                    filter_config=filter_config
                )

                if not created_path:
                    upload_results['failed'] += 1
                    upload_results['failed_chunks'].append({
                        'chunk': idx,
                        'filename': str(chunk_filename),
                        'error': 'Failed to generate FIT file',
                        'records': len(chunk)
                    })
                    continue

                # 上传到 Garmin
                yield SyncProgress(
                    stage="uploading",
                    current=60 + (idx * 30 // total_chunks),
                    total=100,
                    message=f"⬆️ 上传批次 {idx}/{total_chunks} 到 Garmin...",
                    timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                    username=username,
                    details={"chunk": idx, "total_chunks": total_chunks}
                )

                status = garmin_client.upload_fit(chunk_filename)

                if status == "SUCCESS":
                    upload_results['success'] += 1
                    yield SyncProgress(
                        stage="uploading",
                        current=60 + ((idx + 1) * 30 // total_chunks),
                        total=100,
                        message=f"✅ 批次 {idx}/{total_chunks} 上传成功",
                        timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                        username=username,
                        details={"chunk": idx, "status": status}
                    )
                elif status == "DUPLICATE":
                    upload_results['duplicate'] += 1
                    yield SyncProgress(
                        stage="uploading",
                        current=60 + ((idx + 1) * 30 // total_chunks),
                        total=100,
                        message=f"ℹ️ 批次 {idx}/{total_chunks} 数据已存在",
                        timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                        username=username,
                        details={"chunk": idx, "status": status}
                    )
                else:
                    upload_results['failed'] += 1
                    upload_results['failed_chunks'].append({
                        'chunk': idx,
                        'filename': str(chunk_filename),
                        'error': status,
                        'records': len(chunk)
                    })
                    yield SyncProgress(
                        stage="uploading",
                        current=60 + ((idx + 1) * 30 // total_chunks),
                        total=100,
                        message=f"❌ 批次 {idx}/{total_chunks} 上传失败: {status}",
                        timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                        username=username,
                        details={"chunk": idx, "status": status}
                    )

            # 完成
            self.config_mgr.update_last_sync(username)

            if upload_results['failed'] == 0:
                yield SyncProgress(
                    stage="completed",
                    current=100,
                    total=100,
                    message=f"✅ 同步完成！成功 {upload_results['success']} 个批次",
                    timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                    username=username,
                    details=upload_results
                )
            else:
                yield SyncProgress(
                    stage="completed",
                    current=100,
                    total=100,
                    message=f"⚠️ 同步完成，但有 {upload_results['failed']} 个批次失败",
                    timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                    username=username,
                    details=upload_results
                )

        except Exception as e:
            logger.exception(f"同步失败: {e}")
            yield SyncProgress(
                stage="error",
                current=0,
                total=100,
                message=f"❌ 同步失败: {str(e)}",
                timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
                username=username
            )

    def stop_sync(self):
        """停止同步"""
        self._should_stop = True
        logger.info("已设置停止标志")
