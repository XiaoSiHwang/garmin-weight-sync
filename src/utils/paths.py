"""
路径工具函数
处理打包后的应用路径问题
"""
import os
import sys
from pathlib import Path


def get_app_data_dir() -> Path:
    """
    获取应用数据目录（可写）

    在开发环境：返回项目根目录的 data 文件夹
    在打包后：
      - macOS: ~/Library/Application Support/GarminWeightSync
      - Windows: %APPDATA%/GarminWeightSync
      - Linux: ~/.local/share/GarminWeightSync

    Returns:
        Path: 可写的应用数据目录
    """
    # 检测是否在打包环境中运行
    if getattr(sys, 'frozen', False):
        # 打包后的应用
        if sys.platform == 'darwin':
            # macOS
            app_data = Path.home() / 'Library' / 'Application Support' / 'GarminWeightSync'
        elif sys.platform == 'win32':
            # Windows
            app_data = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming')) / 'GarminWeightSync'
        else:
            # Linux
            app_data = Path.home() / '.local' / 'share' / 'GarminWeightSync'
    else:
        # 开发环境：使用项目根目录的 data 文件夹
        # 获取项目根目录（src 的父目录）
        project_root = Path(__file__).parent.parent.parent
        app_data = project_root / 'data'

    # 确保目录存在
    app_data.mkdir(parents=True, exist_ok=True)

    return app_data


def get_session_dir(email: str, custom_base: str = None) -> Path:
    """
    获取 Garmin 会话目录

    Args:
        email: 用户邮箱
        custom_base: 自定义基础路径（可选）

    Returns:
        Path: 会话目录路径
    """
    if custom_base:
        # 使用自定义路径
        base_path = Path(custom_base)
    else:
        # 使用默认的应用数据目录
        base_path = get_app_data_dir()

    session_dir = base_path / '.garth' / email
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def get_output_dir(custom_base: str = None) -> Path:
    """
    获取输出目录（用于 FIT 文件等）

    Args:
        custom_base: 自定义基础路径（可选）

    Returns:
        Path: 输出目录路径
    """
    if custom_base:
        # 使用自定义路径
        base_path = Path(custom_base)
    else:
        # 使用默认的应用数据目录
        base_path = get_app_data_dir()

    output_dir = base_path / 'garmin-fit'
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_config_dir() -> Path:
    """
    获取配置目录

    在打包后的应用中，配置文件应该在可执行文件所在目录

    Returns:
        Path: 配置目录路径
    """
    if getattr(sys, 'frozen', False):
        # 打包后的应用：使用可执行文件所在目录
        if sys.platform == 'darwin':
            # macOS .app 包
            # 可执行文件在 .app/Contents/MacOS/
            # 配置文件应该和 .app 在同一目录
            exe_path = Path(sys.executable)
            app_bundle = exe_path.parent.parent
            config_dir = app_bundle.parent
        else:
            # Windows/Linux：使用可执行文件所在目录
            config_dir = Path(sys.executable).parent
    else:
        # 开发环境：使用项目根目录
        config_dir = Path(__file__).parent.parent.parent

    return config_dir


def get_base_path() -> Path:
    """
    获取项目基础路径，兼容开发和打包环境

    用于定位资源文件（如 logo、配置等）

    Returns:
        Path: 项目基础路径
    """
    if getattr(sys, 'frozen', False):
        # 打包后的应用：使用可执行文件所在目录
        if sys.platform == 'darwin':
            # macOS .app 包
            # 可执行文件在 .app/Contents/MacOS/
            # 资源文件在 .app/Contents/MacOS/ 目录下
            exe_path = Path(sys.executable)
            base_path = exe_path.parent
        else:
            # Windows/Linux：使用可执行文件所在目录
            base_path = Path(sys.executable).parent
    else:
        # 开发环境：使用项目根目录
        base_path = Path(__file__).parent.parent.parent

    return base_path
