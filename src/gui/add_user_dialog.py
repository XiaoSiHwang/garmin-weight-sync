"""
添加用户对话框
向导式对话框,用于添加新的用户配置
"""
from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QRadioButton, QButtonGroup,
    QGroupBox, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt
from typing import Optional, Dict, Any
import base64


class XiaomiPage(QWizardPage):
    """向导第一步: 小米账户信息"""

    # 类常量
    MAX_RETRY_COUNT = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        # 设置页面标题和副标题
        self.setTitle("步骤 1/2: 小米账户")
        self.setSubTitle("请输入小米运动健康账户信息")

        layout = QVBoxLayout()
        layout.setSpacing(20)

        # 用户名/手机号输入
        username_layout = QHBoxLayout()
        username_label = QLabel("用户名/手机号:")
        username_label.setMinimumWidth(120)
        self.username_field = QLineEdit()
        self.username_field.setPlaceholderText("请输入小米账号或手机号")
        self.username_field.setMinimumHeight(35)
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_field)
        layout.addLayout(username_layout)

        # 密码输入
        password_layout = QHBoxLayout()
        password_label = QLabel("密码:")
        password_label.setMinimumWidth(120)
        self.password_field = QLineEdit()
        self.password_field.setPlaceholderText("请输入小米账号密码")
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_field.setMinimumHeight(35)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_field)
        layout.addLayout(password_layout)

        # 设备型号选择
        device_layout = QHBoxLayout()
        device_label = QLabel("设备型号:")
        device_label.setMinimumWidth(120)
        self.device_combo = QComboBox()
        self.device_combo.setMinimumHeight(35)
        self.device_combo.addItem("云米智能体脂秤 MS103", "yunmai.scales.ms103")
        self.device_combo.addItem("云米智能体脂秤 MS1601", "yunmai.scales.ms1601")
        self.device_combo.addItem("云米智能体脂秤 MS1602", "yunmai.scales.ms1602")
        device_layout.addWidget(device_label)
        device_layout.addWidget(self.device_combo)
        layout.addLayout(device_layout)

        # 提示信息
        hint_label = QLabel(
            "提示: 您的小米账号密码将加密保存在本地配置文件中。\n"
            "首次同步时需要完成小米账号登录验证。"
        )
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: #666; font-size: 12px; padding: 10px;")
        layout.addWidget(hint_label)

        layout.addStretch()
        self.setLayout(layout)

        # 注册字段以供向导使用
        self.registerField("xiaomi_username*", self.username_field)
        self.registerField("xiaomi_password*", self.password_field)
        self.registerField("xiaomi_device", self.device_combo, "currentData")

    def _save_xiaomi_data(self, username: str, password: str, model: str, token_data: Dict[str, str]):
        """
        保存小米账户数据到向导

        Args:
            username: 用户名
            password: 密码
            model: 设备型号
            token_data: token 数据字典
        """
        self.wizard().xiaomi_data = {
            "username": username,
            "password": password,
            "model": model,
            "token": token_data
        }

    def validatePage(self) -> bool:
        """验证页面并保存数据"""
        username = self.username_field.text().strip()
        password = self.password_field.text().strip()
        model = self.device_combo.currentData()

        if not username or not password:
            return False

        # 执行小米登录验证
        from xiaomi.login import MiCloudSync
        from gui.auth_dialogs import CaptchaDialog, MfaDialog

        try:
            # 创建 MiCloudSync 实例
            micloud_sync = MiCloudSync(sid="miothealth")

            # 尝试登录
            result = micloud_sync.login(username, password)

            if result.get("ok"):
                # 登录成功,提取 token 数据并保存
                token_data = self._extract_token_data(result, micloud_sync)
                self._save_xiaomi_data(username, password, model, token_data)
                return True

            # 处理验证码
            if captcha_image := result.get("captcha"):
                captcha_result = self._handle_captcha(captcha_image, micloud_sync)
                if captcha_result["success"]:
                    token_data = captcha_result["token"]
                    self._save_xiaomi_data(username, password, model, token_data)
                    return True
                else:
                    # 显示错误信息并阻止继续
                    if captcha_result.get("error"):
                        QMessageBox.critical(
                            self.wizard(),
                            "登录失败",
                            f"验证码验证失败:\n{captcha_result['error']}"
                        )
                    return False

            # 处理 2FA
            if verify_info := result.get("verify"):
                mfa_result = self._handle_mfa(verify_info, micloud_sync)
                if mfa_result["success"]:
                    token_data = mfa_result["token"]
                    self._save_xiaomi_data(username, password, model, token_data)
                    return True
                else:
                    # 显示错误信息并阻止继续
                    if mfa_result.get("error"):
                        QMessageBox.critical(
                            self.wizard(),
                            "登录失败",
                            f"二次验证失败:\n{mfa_result['error']}"
                        )
                    return False

            # 登录失败
            error_msg = str(result.get("exception", "未知错误"))
            QMessageBox.critical(
                self.wizard(),
                "登录失败",
                f"小米账号登录失败:\n{error_msg}"
            )
            return False

        except Exception as e:
            QMessageBox.critical(
                self.wizard(),
                "登录错误",
                f"登录过程发生错误:\n{str(e)}"
            )
            return False

    def _handle_captcha(self, captcha_image: bytes, micloud_sync, retry_count: int = 0) -> Dict[str, Any]:
        """
        处理验证码

        Args:
            captcha_image: 验证码图片的二进制数据
            micloud_sync: MiCloudSync 实例
            retry_count: 当前重试次数

        Returns:
            包含 success 和 token/error 的字典
        """
        # 最多重试 MAX_RETRY_COUNT 次
        if retry_count >= self.MAX_RETRY_COUNT:
            return {
                "success": False,
                "error": "验证码错误次数过多"
            }

        dialog = CaptchaDialog(captcha_image, self.wizard())

        if dialog.exec() == 1:  # Accepted
            code = dialog.get_code()

            # 提交验证码
            result = micloud_sync.login_captcha(code)

            if result.get("ok"):
                # 登录成功
                token_data = self._extract_token_data(result, micloud_sync)
                return {
                    "success": True,
                    "token": token_data
                }
            elif verify_info := result.get("verify"):
                # 需要 2FA - 转发处理
                return self._handle_mfa(verify_info, micloud_sync)
            elif captcha := result.get("captcha"):
                # 验证码错误,重新显示
                QMessageBox.warning(
                    self.wizard(),
                    "验证码错误",
                    f"验证码输入错误,请重试 ({retry_count + 1}/{self.MAX_RETRY_COUNT})"
                )
                return self._handle_captcha(captcha, micloud_sync, retry_count + 1)
            else:
                # 其他错误
                error_msg = str(result.get("exception", "验证码错误"))
                return {
                    "success": False,
                    "error": error_msg
                }
        else:
            # 用户取消
            return {
                "success": False,
                "error": "用户取消"
            }

    def _handle_mfa(self, verify_info: str, micloud_sync, retry_count: int = 0) -> Dict[str, Any]:
        """
        处理二次验证 (2FA)

        Args:
            verify_info: 验证信息
            micloud_sync: MiCloudSync 实例
            retry_count: 当前重试次数

        Returns:
            包含 success 和 token/error 的字典
        """
        # 最多重试 MAX_RETRY_COUNT 次
        if retry_count >= self.MAX_RETRY_COUNT:
            return {
                "success": False,
                "error": "验证码错误次数过多"
            }

        dialog = MfaDialog(verify_info, self.wizard())

        if dialog.exec() == 1:  # Accepted
            ticket = dialog.get_ticket()

            # 提交 2FA 验证码
            result = micloud_sync.login_verify(ticket)

            if result.get("ok"):
                # 登录成功
                token_data = self._extract_token_data(result, micloud_sync)
                return {
                    "success": True,
                    "token": token_data
                }
            else:
                # 验证码错误
                if retry_count < self.MAX_RETRY_COUNT - 1:
                    QMessageBox.warning(
                        self.wizard(),
                        "验证失败",
                        f"二次验证码错误,请重试 ({retry_count + 1}/{self.MAX_RETRY_COUNT})"
                    )
                    return self._handle_mfa(verify_info, micloud_sync, retry_count + 1)
                else:
                    return {
                        "success": False,
                        "error": "二次验证码错误次数过多"
                    }
        else:
            # 用户取消
            return {
                "success": False,
                "error": "用户取消"
            }

    def _extract_token_data(self, result: Dict[str, Any], micloud_sync) -> Dict[str, str]:
        """
        从登录结果中提取 token 数据

        Args:
            result: 登录结果字典
            micloud_sync: MiCloudSync 实例

        Returns:
            包含 userId, passToken, ssecurity 的字典
        """
        # MiCloudSync 返回的 token 格式是 "userId:passToken"
        token_string = result.get("token", "")

        if not token_string:
            return {
                "userId": "",
                "passToken": "",
                "ssecurity": ""
            }

        # 解析 token 字符串
        if ":" in token_string:
            user_id, pass_token = token_string.split(":", 1)
        else:
            user_id = token_string
            pass_token = ""

        # 从 micloud_sync 实例获取 ssecurity (已经是 bytes,需要 base64 编码)
        if micloud_sync.ssecurity:
            ssecurity = base64.b64encode(micloud_sync.ssecurity).decode('utf-8')
        else:
            ssecurity = ""

        return {
            "userId": user_id,
            "passToken": pass_token,
            "ssecurity": ssecurity
        }


class GarminPage(QWizardPage):
    """向导第二步: Garmin 账户信息"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        # 设置页面标题和副标题
        self.setTitle("步骤 2/2: 佳明账户")
        self.setSubTitle("请输入 Garmin Connect 账户信息")

        layout = QVBoxLayout()
        layout.setSpacing(20)

        # 邮箱输入
        email_layout = QHBoxLayout()
        email_label = QLabel("邮箱:")
        email_label.setMinimumWidth(120)
        self.email_field = QLineEdit()
        self.email_field.setPlaceholderText("请输入 Garmin 账号邮箱")
        self.email_field.setMinimumHeight(35)
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_field)
        layout.addLayout(email_layout)

        # 密码输入
        password_layout = QHBoxLayout()
        password_label = QLabel("密码:")
        password_label.setMinimumWidth(120)
        self.password_field = QLineEdit()
        self.password_field.setPlaceholderText("请输入 Garmin 账号密码")
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_field.setMinimumHeight(35)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_field)
        layout.addLayout(password_layout)

        # 服务器域选择
        domain_group = QGroupBox("服务器区域")
        domain_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        domain_layout = QVBoxLayout()
        domain_layout.setSpacing(10)

        self.domain_button_group = QButtonGroup(self)

        # CN 域 (默认选中)
        self.cn_radio = QRadioButton("CN (中国区)")
        self.cn_radio.setChecked(True)
        self.cn_radio.setToolTip("使用 garmin.cn 服务器,适合中国大陆用户")
        domain_layout.addWidget(self.cn_radio)

        # COM 域
        self.com_radio = QRadioButton("COM (国际版)")
        self.com_radio.setToolTip("使用 garmin.com 服务器,适合海外用户")
        domain_layout.addWidget(self.com_radio)

        domain_group.setLayout(domain_layout)
        layout.addWidget(domain_group)

        # 域说明
        domain_hint = QLabel(
            "说明: 中国区用户请选择 CN,海外用户请选择 COM。\n"
            "选择错误可能导致登录失败。"
        )
        domain_hint.setWordWrap(True)
        domain_hint.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(domain_hint)

        # 提示信息
        hint_label = QLabel(
            "提示: 您的 Garmin 账号密码将加密保存在本地配置文件中。\n"
            "如果启用了两步验证,首次同步时需要输入验证码。"
        )
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: #666; font-size: 12px; padding: 10px;")
        layout.addWidget(hint_label)

        layout.addStretch()
        self.setLayout(layout)

        # 注册字段以供向导使用
        self.registerField("garmin_email*", self.email_field)
        self.registerField("garmin_password*", self.password_field)

    def validatePage(self) -> bool:
        """验证页面并保存数据"""
        email = self.email_field.text().strip()
        password = self.password_field.text().strip()
        domain = "CN" if self.cn_radio.isChecked() else "COM"

        if not email or not password:
            return False

        # 保存数据
        self.wizard().garmin_data = {
            "email": email,
            "password": password,
            "domain": domain
        }

        return True


class AddUserDialog(QWizard):
    """添加用户向导对话框"""

    def __init__(self, config_manager, parent=None):
        """
        初始化对话框

        Args:
            config_manager: EnhancedConfigManager 实例
            parent: 父窗口
        """
        super().__init__(parent)

        self.config_manager = config_manager
        self.xiaomi_data: Optional[Dict[str, Any]] = None
        self.garmin_data: Optional[Dict[str, Any]] = None

        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        # 设置窗口属性
        self.setWindowTitle("添加用户")
        self.setMinimumSize(600, 500)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.HelpButtonOnLeft, False)

        # 添加页面
        self.xiaomi_page = XiaomiPage(self)
        self.garmin_page = GarminPage(self)

        self.addPage(self.xiaomi_page)
        self.addPage(self.garmin_page)

    def getXiaomiData(self) -> Optional[Dict[str, Any]]:
        """获取小米账户数据"""
        return self.xiaomi_data

    def getGarminData(self) -> Optional[Dict[str, Any]]:
        """获取 Garmin 账户数据"""
        return self.garmin_data

    def get_user_data(self) -> Optional[Dict[str, Any]]:
        """获取完整的用户数据"""
        if not self.xiaomi_data or not self.garmin_data:
            return None

        return {
            **self.xiaomi_data,
            "garmin": self.garmin_data
        }
