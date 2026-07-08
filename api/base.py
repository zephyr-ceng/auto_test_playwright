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
        self.__config_path = config_path
        self.__logger = logger or Logger("Read_Environment")
        self.__yaml = YamlManager(self.__logger)
        self.__values: Dict[str, Any] = {}
        self.reload()

    def reload(self) -> Dict[str, Any]:
        """重新加载 environment.yaml，并将顶层配置项注入为实例属性。"""
        config = self.__yaml.read(self.__config_path)
        if not isinstance(config, dict) or not config:
            raise RuntimeError(f"environment config not configured in {self.__config_path}")

        self.__values = dict(config)
        for key, value in self.__values.items():
            if isinstance(key, str) and key.isidentifier():
                setattr(self, key, value)
        return self.as_dict()

    def get(self, key: str, default: Any = None) -> Any:
        """按 key 获取环境配置；key 不存在时返回默认值。"""
        return self.__values.get(key, default)

    def require(self, key: str) -> Any:
        """按 key 获取必填环境配置；配置缺失或为空时立即报错。"""
        value = self.get(key)
        if value in (None, ""):
            raise RuntimeError(f"{key} not configured in {self.__config_path}")
        return value

    def as_dict(self) -> Dict[str, Any]:
        """返回已加载环境配置的浅拷贝。"""
        return dict(self.__values)
