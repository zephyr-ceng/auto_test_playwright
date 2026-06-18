import pytest

from api.base import ApiEnvironmentConfig


@pytest.fixture(scope="session")
def api_env():
    """读取 API 测试环境配置，整个测试会话复用一次。"""
    return ApiEnvironmentConfig()


@pytest.fixture(scope="session")
def base_url(api_env):
    """返回 API 基础地址，供所有接口客户端复用。"""
    return api_env.require("baseUrl")


@pytest.fixture(scope="session")
def gateway_url(api_env):
    return api_env.require("gatewayUrl")
