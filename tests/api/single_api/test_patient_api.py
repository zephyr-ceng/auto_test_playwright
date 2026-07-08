from pathlib import Path
from hashlib import md5

import allure
import pytest

from api.common.assertions import assert_business_code, assert_response_json, assert_status_code_2xx
from api.common.client import HTTPClient
from api.login_verification.login import Login
from api.paitent_manager.patient_api import PatientAPIS
from utils.random_manager import RandomManager

PATIENT_ID_KEYS = ("id", "ID", "patientID", "patientId")
DEFAULT_ATTACHMENT_TAG = "ct"
DEFAULT_ATTACHMENT_TYPE = "dcm"
DEFAULT_ATTACHMENT_JAW_TYPE = "upper"


def _file_md5(file_path: Path) -> str:
    """计算测试附件 MD5，保证初始化上传参数和实际上传文件一致。"""
    hash_obj = md5()
    with file_path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def _extract_patient_id(response_body: dict) -> str:
    """从患者接口响应 data 中提取患者 ID，并兼容不同返回字段名。"""
    data = response_body.get("data")
    assert isinstance(data, dict), f"患者响应 data 不是对象，响应: {response_body}"
    patient_id = next((data.get(key) for key in PATIENT_ID_KEYS if data.get(key) not in (None, "")), None)
    assert patient_id is not None, f"患者响应未包含患者 ID，响应: {response_body}"
    return str(patient_id)


def _create_patient_and_get_id(patient_api, patient_data: dict | None = None) -> str:
    """创建临时测试患者并返回患者 ID，供依赖患者数据的单接口用例使用。"""
    request_data = patient_data or {
        "name": f"AP_{RandomManager.random_chinese_name()}",
        "gender": 1,
        "date_of_birth": 631123200000,
        "telephone": RandomManager.random_phone(),
    }
    response = patient_api.add_patient(**request_data)
    assert_status_code_2xx(response)
    response_body = assert_response_json(response)
    assert_business_code(response_body, 0)
    return _extract_patient_id(response_body)


def _delete_patient_if_created(patient_api, patient_id: str | None) -> None:
    """删除当前用例创建的临时患者，避免测试数据残留。"""
    if not patient_id:
        return
    response = patient_api.delete_patient(patient_id=patient_id)
    assert_status_code_2xx(response)
    response_body = assert_response_json(response)
    assert_business_code(response_body, 0)


@pytest.fixture(scope="session")
def auth_session_cookie(base_url, gateway_url, api_env):
    """测试会话内登录一次，让 gateway 接口复用注入的 sessionCookie。"""
    client = HTTPClient(base_url=base_url, gateway_url=gateway_url)
    try:
        Login(client).login_by_username(api_env.require("username"), api_env.require("password"))
    finally:
        client.session.close()


@pytest.fixture(scope="function")
def http_client(base_url, gateway_url):
    """创建可调用普通接口和 gateway 接口的 HTTP 客户端。"""
    client = HTTPClient(base_url=base_url, gateway_url=gateway_url)
    yield client
    client.session.close()


@pytest.fixture(scope="function")
def patient_api(http_client, auth_session_cookie):
    """创建患者接口封装，gateway 鉴权由 sessionCookie 注入完成。"""
    return PatientAPIS(http_client)


@allure.feature("患者接口")
class TestPatientAPI:
    """患者 gateway 接口测试。"""

    @pytest.mark.api
    @allure.story("新增患者")
    # name 为空时，当前接口仍按业务 code=0 校验；前端负责必填校验。
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
        """新增随机患者并校验成功响应中包含患者 ID。"""
        patient_id = None
        try:
            response = patient_api.add_patient(**patient_data)

            assert_status_code_2xx(response)
            response_body = assert_response_json(response)
            assert_business_code(response_body, 0)

            patient_id = _extract_patient_id(response_body)
        finally:
            # 新增接口会产生测试患者，校验完成后立即删除，避免数据残留。
            _delete_patient_if_created(patient_api, patient_id)

    @pytest.mark.api
    @allure.story("修改患者")
    @pytest.mark.parametrize(
        "patient_updates",
        [
            {"name": f"AP_{RandomManager.random_chinese_name()}_U"},
            {"gender": 2},
            {"date_of_birth": 662659200000},
            {"telephone": RandomManager.random_phone()},
            {"desc": "update patient by api"},
            {
                "name": f"AP_{RandomManager.random_chinese_name()}_U",
                "gender": 2,
                "date_of_birth": 662659200000,
                "identity_card": "",
                "telephone": RandomManager.random_phone(),
                "desc": "update patient by api",
            },
        ],
        ids=[
            "update_name",
            "update_gender",
            "update_date_of_birth",
            "update_telephone",
            "update_desc",
            "update_all_fields",
        ],
    )
    def test_update_patient_success(self, patient_api, patient_updates) -> None:
        """修改随机患者并校验 gateway 成功响应。"""
        patient_id = _create_patient_and_get_id(patient_api)
        try:
            update_response = patient_api.update_patient(patient_id=patient_id, **patient_updates)

            assert_status_code_2xx(update_response)
            update_response_body = assert_response_json(update_response)
            assert_business_code(update_response_body, 0)
        finally:
            # 修改接口依赖临时患者，测试完成后删除前置数据。
            _delete_patient_if_created(patient_api, patient_id)

    @pytest.mark.api
    @allure.story("分页查询患者")
    def test_query_patient_page_success(self, patient_api) -> None:
        """分页查询患者并校验列表和总数字段。"""
        patient_name = f"AP_{RandomManager.random_chinese_name()}"
        patient_phone = RandomManager.random_phone()
        patient_id = _create_patient_and_get_id(
            patient_api,
            {
                "name": patient_name,
                "gender": 1,
                "date_of_birth": 631123200000,
                "telephone": patient_phone,
            },
        )

        try:
            response = patient_api.query_patient_page(
                page_index=1,
                page_size=10,
                name=patient_name,
                gender=1,
                telephone=patient_phone,
            )

            assert_status_code_2xx(response)
            response_body = assert_response_json(response)
            assert_business_code(response_body, 0)
            data = response_body.get("data")
            assert isinstance(data, dict), f"分页查询患者响应 data 不是对象，响应: {response_body}"
            assert any(data.get(key) is not None for key in ("data", "list", "records")), (
                f"分页查询患者响应未包含列表字段，响应: {response_body}"
            )
            assert data.get("total") is not None, f"分页查询患者响应未包含 total，响应: {response_body}"
        finally:
            # 分页查询为验证筛选条件创建了临时患者，查询完成后删除。
            _delete_patient_if_created(patient_api, patient_id)

    @pytest.mark.api
    @allure.story("查询患者详情")
    def test_query_patient_detail_v2_success(self, patient_api) -> None:
        """查询患者详情 V2 并校验返回患者 ID。"""
        patient_id = _create_patient_and_get_id(patient_api)
        try:
            response = patient_api.query_patient_detail_v2(patient_id=patient_id)

            assert_status_code_2xx(response)
            response_body = assert_response_json(response)
            # print(response_body)
            assert_business_code(response_body, 0)
            data = response_body.get("data")
            assert isinstance(data, dict), f"查询患者详情响应 data 不是对象，响应: {response_body}"
            detail_patient_id = next((data.get(key) for key in PATIENT_ID_KEYS if data.get(key) not in (None, "")),
                                     None)
            assert detail_patient_id is not None, f"查询患者详情响应未包含患者 ID，响应: {response_body}"
        finally:
            # 查询详情用例创建了临时患者，断言结束后删除，避免影响后续接口测试。
            _delete_patient_if_created(patient_api, patient_id)

    @pytest.mark.api
    @allure.story("附件上传")
    @pytest.mark.parametrize(
        "file_path",
        [
            Path("data/dicom/wujia"),
        ],
        ids=["吴佳"],
    )
    def test_file_upload(self, patient_api, file_path: Path) -> None:
        """按初始化、上传分片、完成上传的顺序校验附件上传成功。"""
        patient_api.start_file_upload()
