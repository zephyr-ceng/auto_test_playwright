from typing import Any, Optional

from utils.yaml_reader import YamlManager
from utils.logger import Logger
from core.base_page import BasePage


class ConfigValue:
    """配置读取基类：

    - 默认从项目根目录读取 'config.yaml'（可通过 config_path 覆盖）
    - 使用 utils.YamlManager 读取文件（需要 logger）
    - 读取后将顶层键作为属性注入到实例中，子类可直接访问如 self.some_key
    - 提供 get/reload 方法
    """

    def __init__(self, config_path: str = "config/config.yaml", logger: Optional[Logger] = None):
        # 如果没有提供 logger，则创建一个内部 logger
        self._logger = logger or Logger("config")
        ym = YamlManager(self._logger)
        config = ym.read(config_path)
        if not config:
            raise RuntimeError(f"config_path not configured in {config_path}")
        self.remote_url = config.get("remote_url")
        self.base_url = config.get("base_url")
        self.username = config.get("username")
        self.password = config.get("password")
        self.cookies_write_time = config.get("cookies_write_time")
        self.cookies = config.get("cookies")
        if not self.username or not self.password or not self.base_url or not self.cookies_write_time or not self.cookies:
            raise RuntimeError(f"username/password/base_url not configured in {config_path}")


class LoginPage(BasePage, ConfigValue):
    def __init__(
            self,
            driver: Any,
            logger: Optional[Any] = None,
            locators_path: str = "data/login_data.yaml",
            config_path: str = "config/config.yaml",
    ):
        BasePage.__init__(driver, logger)
        ConfigValue.__init__(self, config_path, logger)
        self._config = YamlManager(self.logger)

        # config.yaml
        self._config_path = config_path
        print(self.base_url)


if __name__ == "__main__":
    from utils.logger import Logger

    log = Logger("config")
    cv = LoginPage(config_path="config/config.yaml", logger=log)
    # cv = ConfigValue()
    print(cv.username)
    print(cv.remote_url)
    print(cv.base_url)
