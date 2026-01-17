"""
PyInstaller Runtime Hook
修复打包后 inspect.getsource() 失败的问题

优化：延迟 patching 以减少启动时间开销
"""
import sys
import os

# 禁用 logfire 的 pydantic 集成（会导致 inspect.getsource 错误）
os.environ['LOGFIRE_SKIP_PYDANTIC_PLUGIN'] = '1'
os.environ['PYDANTIC_DISABLE_PYDANTIC_V2_PLUGINS'] = '1'

# 延迟 patching - 只在首次调用时执行
_Patched = False

def _patch_inspect():
    """延迟 patching inspect 模块"""
    global _Patched
    if _Patched:
        return
    _Patched = True

    import inspect

    _original_getsource = inspect.getsource

    def _patched_getsource(object):
        """修补后的 getsource，在打包环境中返回空字符串"""
        try:
            return _original_getsource(object)
        except (OSError, TypeError):
            return "# Source code not available in frozen application"

    inspect.getsource = _patched_getsource

    _original_getsourcelines = inspect.getsourcelines

    def _patched_getsourcelines(object):
        """修补后的 getsourcelines"""
        try:
            return _original_getsourcelines(object)
        except (OSError, TypeError):
            return ["# Source code not available in frozen application"], 1

    inspect.getsourcelines = _patched_getsourcelines

    _original_getsourcefile = inspect.getsourcefile

    def _patched_getsourcefile(object):
        """修补后的 getsourcefile"""
        try:
            return _original_getsourcefile(object)
        except (OSError, TypeError):
            return None

    inspect.getsourcefile = _patched_getsourcefile

# 延迟 patching 到首次调用 inspect 时
import inspect as _inspect_module
_original_getsource = _inspect_module.getsource

def _lazy_getsource(object):
    _patch_inspect()
    return _inspect_module.getsource(self=object)

_inspect_module.getsource = _lazy_getsource
