"""
认证对话框
用于处理小米登录的验证码和 2FA 输入
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QWidget
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from typing import Optional
import io


class CaptchaDialog(QDialog):
    """验证码输入对话框"""

    def __init__(self, captcha_image: bytes, parent=None):
        """
        初始化验证码对话框

        Args:
            captcha_image: 验证码图片的二进制数据
            parent: 父窗口
        """
        super().__init__(parent)
        self.captcha_code = None
        self.captcha_image = captcha_image

        self.setWindowTitle("小米账号验证码")
        self.setModal(True)
        self.setMinimumSize(450, 350)
        self.setMaximumSize(450, 350)

        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("请输入验证码")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 验证码图片
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 将二进制数据转换为 QPixmap
        image = QImage.fromData(self.captcha_image)
        pixmap = QPixmap.fromImage(image)

        # 缩放图片以适应窗口
        scaled_pixmap = pixmap.scaled(
            300, 100,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        image_label.setPixmap(scaled_pixmap)
        layout.addWidget(image_label)

        # 提示文字
        hint_label = QLabel("如果看不清,可以取消后重新登录获取新验证码")
        hint_label.setStyleSheet("color: #666; font-size: 11px;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)

        # 输入框
        input_layout = QHBoxLayout()
        input_label = QLabel("验证码:")
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("请输入上图中的验证码")
        self.input_field.setMaxLength(10)
        self.input_field.setMinimumHeight(35)
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_field)
        layout.addLayout(input_layout)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("取消")
        cancel_button.setMinimumWidth(100)
        cancel_button.setMinimumHeight(35)
        cancel_button.clicked.connect(self.reject)

        ok_button = QPushButton("确定")
        ok_button.setMinimumWidth(100)
        ok_button.setMinimumHeight(35)
        ok_button.setDefault(True)
        ok_button.clicked.connect(self.accept)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 设置焦点到输入框
        self.input_field.setFocus()

    def get_code(self) -> str:
        """获取用户输入的验证码"""
        return self.captcha_code if self.captcha_code else ""

    def accept(self):
        """确认按钮点击"""
        code = self.input_field.text().strip()

        if not code:
            QMessageBox.warning(self, "提示", "请输入验证码")
            self.input_field.setFocus()
            return

        self.captcha_code = code
        super().accept()


class MfaDialog(QDialog):
    """二次验证码(2FA)输入对话框"""

    def __init__(self, verify_info: str, parent=None):
        """
        初始化 2FA 对话框

        Args:
            verify_info: 验证信息(描述需要哪种验证方式)
            parent: 父窗口
        """
        super().__init__(parent)
        self.verify_code = None
        self.verify_info = verify_info

        self.setWindowTitle("小米账号二次验证")
        self.setModal(True)
        self.setMinimumSize(400, 200)
        self.setMaximumSize(400, 200)

        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("需要二次验证")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 说明文字
        info_label = QLabel(self.verify_info)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #333; font-size: 13px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        # 详细说明
        detail_label = QLabel("请输入发送到您手机或邮箱的验证码")
        detail_label.setStyleSheet("color: #666; font-size: 12px;")
        detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(detail_label)

        # 输入框
        input_layout = QHBoxLayout()
        input_label = QLabel("验证码:")
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("请输入6位验证码")
        self.input_field.setMaxLength(10)
        self.input_field.setMinimumHeight(35)
        self.input_field.setEchoMode(QLineEdit.EchoMode.Normal)  # 正常显示输入
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_field)
        layout.addLayout(input_layout)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("取消")
        cancel_button.setMinimumWidth(100)
        cancel_button.setMinimumHeight(35)
        cancel_button.clicked.connect(self.reject)

        ok_button = QPushButton("确定")
        ok_button.setMinimumWidth(100)
        ok_button.setMinimumHeight(35)
        ok_button.setDefault(True)
        ok_button.clicked.connect(self.accept)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 设置焦点到输入框
        self.input_field.setFocus()

    def get_ticket(self) -> str:
        """获取用户输入的验证码"""
        return self.verify_code if self.verify_code else ""

    def accept(self):
        """确认按钮点击"""
        code = self.input_field.text().strip()

        if not code:
            QMessageBox.warning(self, "提示", "请输入验证码")
            self.input_field.setFocus()
            return

        self.verify_code = code
        super().accept()


class GarminMfaDialog(QDialog):
    """Garmin 两步验证码(MFA)输入对话框"""

    def __init__(self, email: str, parent=None):
        """
        初始化 Garmin MFA 对话框

        Args:
            email: Garmin 账号邮箱
            parent: 父窗口
        """
        super().__init__(parent)
        self.mfa_code = None
        self.email = email

        self.setWindowTitle("Garmin 两步验证")
        self.setModal(True)
        self.setMinimumSize(400, 220)
        self.setMaximumSize(400, 220)

        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("需要两步验证")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 账号信息
        account_label = QLabel(f"账号: {self.email}")
        account_label.setStyleSheet("color: #333; font-size: 13px;")
        account_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(account_label)

        # 说明文字
        detail_label = QLabel("请输入 Garmin发送至手机或邮箱的二次验证码")
        detail_label.setWordWrap(True)
        detail_label.setStyleSheet("color: #666; font-size: 12px;")
        detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(detail_label)

        # 输入框
        input_layout = QHBoxLayout()
        input_label = QLabel("验证码:")
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("请输入6位验证码")
        self.input_field.setMaxLength(6)
        self.input_field.setMinimumHeight(35)
        self.input_field.setEchoMode(QLineEdit.EchoMode.Normal)  # 正常显示输入
        self.input_field.setAlignment(Qt.AlignmentFlag.AlignCenter)
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_field)
        layout.addLayout(input_layout)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("取消")
        cancel_button.setMinimumWidth(100)
        cancel_button.setMinimumHeight(35)
        cancel_button.clicked.connect(self.reject)

        ok_button = QPushButton("确定")
        ok_button.setMinimumWidth(100)
        ok_button.setMinimumHeight(35)
        ok_button.setDefault(True)
        ok_button.clicked.connect(self.accept)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 设置焦点到输入框
        self.input_field.setFocus()

    def get_mfa_code(self) -> str:
        """获取用户输入的验证码"""
        return self.mfa_code if self.mfa_code else ""

    def accept(self):
        """确认按钮点击"""
        code = self.input_field.text().strip()

        if not code:
            QMessageBox.warning(self, "提示", "请输入验证码")
            self.input_field.setFocus()
            return

        if len(code) != 6 or not code.isdigit():
            QMessageBox.warning(self, "提示", "请输入6位数字验证码")
            self.input_field.setFocus()
            return

        self.mfa_code = code
        super().accept()
