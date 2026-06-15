from typing import Any, Dict, Optional

from utils.logger import Logger
from utils.yaml_reader import YamlManager


class ApiEnvironmentConfig:
    """读取 API 测试环境变量配置。"""

    def __init__(
            self,
            config_path: str = "config/environment.yaml",
            logger: Optional[Logger] = None,
    ) -> None:
        self._config_path = config_path
        self._logger = logger or Logger("Read_Environment")
        self._yaml = YamlManager(self._logger)
        self._values: Dict[str, Any] = {}
        self.reload()

    def reload(self) -> Dict[str, Any]:
        """重新加载 environment.yaml，并将顶层配置项注入为实例属性。"""
        config = self._yaml.read(self._config_path)
        if not isinstance(config, dict) or not config:
            raise RuntimeError(f"environment config not configured in {self._config_path}")

        self._values = dict(config)
        for key, value in self._values.items():
            if isinstance(key, str) and key.isidentifier():
                setattr(self, key, value)
        return self.as_dict()

    def get(self, key: str, default: Any = None) -> Any:
        """按 key 获取环境配置；key 不存在时返回默认值。"""
        return self._values.get(key, default)

    def require(self, key: str) -> Any:
        """按 key 获取必填环境配置；配置缺失或为空时立即报错。"""
        value = self.get(key)
        if value in (None, ""):
            raise RuntimeError(f"{key} not configured in {self._config_path}")
        return value

    def as_dict(self) -> Dict[str, Any]:
        """返回已加载环境配置的浅拷贝。"""
        return dict(self._values)
