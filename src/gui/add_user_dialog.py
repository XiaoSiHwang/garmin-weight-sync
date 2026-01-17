"""
添加用户对话框
向导式对话框,用于添加新的用户配置
"""
from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QRadioButton, QButtonGroup,
    QGroupBox, QWidget
)
from PyQt6.QtCore import Qt
from typing import Optional, Dict, Any


class XiaomiPage(QWizardPage):
    """向导第一步: 小米账户信息"""

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

    def validatePage(self) -> bool:
        """验证页面输入"""
        username = self.username_field.text().strip()
        password = self.password_field.text().strip()

        if not username:
            self.wizard().setError("请输入用户名或手机号")
            return False

        if not password:
            self.wizard().setError("请输入密码")
            return False

        return True


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
        """验证页面输入"""
        email = self.email_field.text().strip()
        password = self.password_field.text().strip()

        if not email:
            self.wizard().setError("请输入 Garmin 账号邮箱")
            return False

        if "@" not in email:
            self.wizard().setError("请输入有效的邮箱地址")
            return False

        if not password:
            self.wizard().setError("请输入 Garmin 账号密码")
            return False

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
        self._error_message: Optional[str] = None

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

        # 连接信号
        self.finished.connect(self._on_finished)

    def setError(self, message: str):
        """设置错误消息"""
        self._error_message = message

    def getError(self) -> Optional[str]:
        """获取错误消息"""
        return self._error_message

    def _on_finished(self, result: int):
        """向导完成时的回调"""
        if result == QWizard.DialogCode.Accepted:
            # 收集小米账户数据
            self.xiaomi_data = {
                "username": self.field("xiaomi_username"),
                "password": self.field("xiaomi_password"),
                "model": self.field("xiaomi_device")
            }

            # 收集 Garmin 账户数据
            self.garmin_data = {
                "email": self.field("garmin_email"),
                "password": self.field("garmin_password"),
                "domain": "CN" if self.garmin_page.cn_radio.isChecked() else "COM"
            }

    def getXiaomiData(self) -> Optional[Dict[str, Any]]:
        """获取小米账户数据"""
        return self.xiaomi_data

    def getGarminData(self) -> Optional[Dict[str, Any]]:
        """获取 Garmin 账户数据"""
        return self.garmin_data

    def getUserData(self) -> Optional[Dict[str, Any]]:
        """获取完整的用户数据"""
        if not self.xiaomi_data or not self.garmin_data:
            return None

        return {
            **self.xiaomi_data,
            "garmin": self.garmin_data
        }
