"""TTS 引擎注册表与工厂函数"""

from ._base import TTSEngine

_ENGINE_REGISTRY: dict[str, type[TTSEngine]] = {}


def register_engine(cls: type[TTSEngine]) -> type[TTSEngine]:
    """注册引擎类的装饰器。在类上设置 _engine_name 后调用。"""
    engine_name = getattr(cls, "_engine_name", None) or cls.name  # type: ignore[attr-defined]
    _ENGINE_REGISTRY[engine_name] = cls
    return cls


def get_engine(name: str, config: dict) -> TTSEngine:
    """根据名称实例化引擎。"""
    _ensure_loaded()
    if name not in _ENGINE_REGISTRY:
        available = ", ".join(_ENGINE_REGISTRY.keys()) or "(无)"
        raise ValueError(
            f"未知引擎 '{name}'，可用引擎: {available}"
        )
    engine_config = config.get("engines", {}).get(name, {})
    return _ENGINE_REGISTRY[name](engine_config)


def list_available_engines() -> list[str]:
    """列出所有已注册的引擎名称。"""
    _ensure_loaded()
    return list(_ENGINE_REGISTRY.keys())


_LOADED = False


def _ensure_loaded() -> None:
    """确保所有引擎模块已导入（触发注册）。"""
    global _LOADED
    if _LOADED:
        return
    _LOADED = True
    from . import edge_tts as _edge
    from . import kokoro_engine as _kokoro
    from . import openai_engine as _openai
    from . import pyttsx3_engine as _pyttsx3
    from . import system as _system

    # 触发模块级注册
    _edge, _kokoro, _openai, _pyttsx3, _system
