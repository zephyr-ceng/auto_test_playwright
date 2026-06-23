import allure
import pytest

from api.common.assertions import assert_business_code, assert_response_json, assert_status_code_2xx
from api.common.client import HTTPClient
from api.login_verification.login import Login
from api.paitent_manager.patient_api import PatientAPIS
from utils.random_manager import RandomManager


@pytest.fixture(scope="session")
def auth_session_cookie(base_url, gateway_url, api_env):
    """Login once per test session so gateway APIs can use injected sessionCookie."""
    client = HTTPClient(base_url=base_url, gateway_url=gateway_url)
    try:
        Login(client).login_by_username(api_env.require("username"), api_env.require("password"))
    finally:
        client.session.close()


@pytest.fixture(scope="function")
def http_client(base_url, gateway_url):
    """Create an HTTP client that can call both normal and gateway APIs."""
    client = HTTPClient(base_url=base_url, gateway_url=gateway_url)
    yield client
    client.session.close()


@pytest.fixture(scope="function")
def patient_api(http_client, auth_session_cookie):
    """Create a patient API wrapper; gateway auth comes from injected sessionCookie."""
    return PatientAPIS(http_client)


@allure.feature("Patient API")
class TestPatientAPI:
    """Patient gateway API tests."""

    @pytest.mark.api
    @allure.story("Add patient")
    # not_name 应该返回的是错误处理的code,前端做了必填的验证
    @pytest.mark.parametrize(
        "patient_data",
        [
            {"name": f"AP_{RandomManager.random_chinese_name()}"},
            {"name": f"AP_{RandomManager.random_chinese_name()}", "gender": 1},
            {"name": f"AP_{RandomManager.random_chinese_name()}", "date_of_birth": 631123200000},
            {"name": f"AP_{RandomManager.random_chinese_name()}", "identity_card": ""},
            {"name": f"AP_{RandomManager.random_chinese_name()}", "telephone": RandomManager.random_phone()},
            {"name": f"AP_{RandomManager.random_chinese_name()}", "desc": ""},
            {
                "name": f"AP_{RandomManager.random_chinese_name()}",
                "gender": 1,
                "date_of_birth": 631123200000,
                "identity_card": "",
                "telephone": RandomManager.random_phone(),
                "desc": "",
            },
            {
                "name": "",
                "gender": 1,
                "date_of_birth": 631123200000,
                "identity_card": "",
                "telephone": "",
                "desc": ""
            }
        ],
        ids=[
            "name_only",
            "with_gender",
            "with_date_of_birth",
            "with_identity_card",
            "with_telephone",
            "with_desc",
            "all_fields",
            "not_name"
        ],
    )
    def test_add_patient_success(self, patient_api, patient_data) -> None:
        """Create a random patient and verify the success response includes a patient ID."""
        allure.dynamic.title("Add patient returns patient ID")

        response = patient_api.add_patient(**patient_data)

        assert_status_code_2xx(response)
        response_body = assert_response_json(response)
        assert_business_code(response_body, 0)

        data = response_body.get("data")
        assert isinstance(data, dict), f"add patient response data is not an object, response: {response_body}"
        assert any(data.get(key) not in (None, "") for key in ("id", "ID", "patientID", "patientId")), (
            f"add patient response does not include patientID, response: {response_body}"
        )
