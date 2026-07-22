from hashlib import md5
from pathlib import Path
from typing import Any

import allure
import pytest

from api.common.assertions import assert_business_code, assert_response_json, assert_status_code_2xx
from api.common.client import HTTPClient
from api.file.file_api import FileAPI
from api.login_verification.login import Login
from api.paitent_manager.patient_api import PatientAPIS
from utils.random_manager import RandomManager

PATIENT_ID_KEYS = ("id", "ID", "patientID", "patientId")
WUJIA_DICOM_DIR = Path("data/dicom/wujia")
CT_FILE_NAME = "handled_origin_data"
CT_ENTRY_POINT = 1
CT_BIND_TAGS = ["ct"]
CT_BIND_TYPE = "dcm"
CT_BIND_PARAMS = "{}"
CT_BIND_JAW_TYPE = "upper"
CT_BIND_TREATMENT_ID = "0"


def _extract_patient_id(response_body: dict[str, Any]) -> str:
    """从新增患者响应中提取患者 ID。"""
    data = response_body.get("data")
    assert isinstance(data, dict), f"患者响应 data 不是对象，响应: {response_body}"
    patient_id = next((data.get(key) for key in PATIENT_ID_KEYS if data.get(key) not in (None, "")), None)
    assert patient_id is not None, f"患者响应未包含患者 ID，响应: {response_body}"
    return str(patient_id)


def _create_patient_and_get_id(patient_api: PatientAPIS) -> str:
    """创建 CT 上传链路使用的临时患者。"""
    response = patient_api.add_patient(
        name=f"AP_{RandomManager.random_chinese_name()}",
        gender=1,
        date_of_birth=631123200000,
        telephone=RandomManager.random_phone(),
    )
    assert_status_code_2xx(response)
    response_body = assert_response_json(response)
    assert_business_code(response_body, 0)
    return _extract_patient_id(response_body)


def _delete_patient_if_created(patient_api: PatientAPIS, patient_id: str | None) -> None:
    """删除临时患者，避免端到端用例残留数据。"""
    if not patient_id:
        return
    response = patient_api.delete_patient(patient_id=patient_id)
    assert_status_code_2xx(response)
    response_body = assert_response_json(response)
    assert_business_code(response_body, 0)


def _unbind_file_if_bound(patient_api: PatientAPIS, patient_id: str | None, file_key: str | None) -> None:
    """解绑当前用例绑定的 CT 文件。"""
    if not patient_id or not file_key:
        return
    response = patient_api.unbind_model_file_to_patient(patient_id=patient_id, file_key=file_key)
    assert_status_code_2xx(response)
    response_body = assert_response_json(response)
    assert_business_code(response_body, 0)


def _wujia_dicom_files() -> list[Path]:
    """读取 wujia 目录下的 DICOM 序列文件。"""
    if not WUJIA_DICOM_DIR.exists():
        pytest.skip(f"缺少 DICOM 测试目录: {WUJIA_DICOM_DIR}")

    dicom_files = sorted(path for path in WUJIA_DICOM_DIR.iterdir() if path.is_file() and path.suffix.lower() == ".dcm")
    if not dicom_files:
        pytest.skip(f"DICOM 测试目录中没有 .dcm 文件: {WUJIA_DICOM_DIR}")
    return dicom_files


def _file_md5(file_path: Path) -> str:
    """计算单个 DICOM 文件 MD5。"""
    hash_obj = md5()
    with file_path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def _build_wujia_upload_manifest() -> list[dict[str, Any]]:
    """按每个 DICOM 文件一个 part 构建上传清单。"""
    dicom_files = _wujia_dicom_files()
    upload_parts: list[dict[str, Any]] = []

    for part_id, dicom_file in enumerate(dicom_files, start=1):
        file_length = dicom_file.stat().st_size
        part_md5 = _file_md5(dicom_file)
        upload_parts.append(
            {
                "part_id": part_id,
                "file_path": dicom_file,
                "file_size": file_length,
                "md5": part_md5,
            }
        )

    return upload_parts


def _extract_first_key_value(value: Any, keys: tuple[str, ...]) -> Any:
    """递归提取响应中出现的第一个指定字段。"""
    if isinstance(value, dict):
        for key in keys:
            item = value.get(key)
            if item not in (None, ""):
                return item
        for item in value.values():
            found = _extract_first_key_value(item, keys)
            if found not in (None, ""):
                return found
    if isinstance(value, list):
        for item in value:
            found = _extract_first_key_value(item, keys)
            if found not in (None, ""):
                return found
    return None


def _extract_complete_file_key(response_body: dict[str, Any]) -> str:
    """从 11001 响应中提取完整 CT 主 fileKey。"""
    data = response_body.get("data")
    assert isinstance(data, dict), f"创建完整 CT 响应 data 不是对象，响应: {response_body}"
    file_key = _extract_first_key_value(data, ("fileKey", "filekey", "file_keys", "fileKeys"))
    if isinstance(file_key, list):
        file_key = next((item for item in file_key if item not in (None, "")), None)
    assert file_key not in (None, ""), f"创建完整 CT 响应未包含 fileKey，响应: {response_body}"
    return str(file_key)


def _extract_file_list(patient_detail: dict[str, Any]) -> list[Any]:
    """从患者详情响应中兼容提取文件列表。"""
    candidates = [
        patient_detail.get("files"),
        patient_detail.get("fileList"),
        patient_detail.get("modelFiles"),
        patient_detail.get("medicalFiles"),
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return candidate
    return []


def _contains_file_key(value: Any, file_key: str) -> bool:
    """递归检查响应结构中是否包含目标 fileKey。"""
    if isinstance(value, dict):
        return any(_contains_file_key(item, file_key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_file_key(item, file_key) for item in value)
    return value == file_key


def _extract_file_description(response_body: dict[str, Any], file_key: str) -> Any:
    """从文件描述响应中兼容提取目标文件描述。"""
    data = response_body.get("data")
    assert data not in (None, ""), f"查询文件描述响应 data 为空，响应: {response_body}"
    if isinstance(data, dict):
        if file_key in data:
            return data[file_key]
        files = data.get("files")
        if isinstance(files, list):
            return next((item for item in files if _contains_file_key(item, file_key)), None)
    if isinstance(data, list):
        return next((item for item in data if _contains_file_key(item, file_key)), None)
    return None


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
    client = HTTPClient(base_url=base_url, gateway_url=gateway_url, timeout=60)
    yield client
    client.session.close()


@pytest.fixture(scope="function")
def file_api(http_client, auth_session_cookie):
    """创建文件接口封装，gateway 鉴权由 sessionCookie 注入完成。"""
    return FileAPI(http_client)


@pytest.fixture(scope="function")
def patient_api(http_client, auth_session_cookie):
    """创建患者接口封装，gateway 鉴权由 sessionCookie 注入完成。"""
    return PatientAPIS(http_client)


@allure.feature("CT 附件上传")
class TestFileAPI:
    """CT 附件上传和患者绑定端到端接口测试。"""

    @pytest.mark.api
    @pytest.mark.destructive_api
    @allure.story("wujia DICOM 序列上传并绑定患者")
    def test_upload_wujia_ct_and_bind_patient_success(self, file_api, patient_api) -> None:
        """逐个上传 wujia DICOM 分片，创建完整 CT 主 fileKey 后绑定临时患者并查询校验。"""
        upload_parts = _build_wujia_upload_manifest()
        patient_id = _create_patient_and_get_id(patient_api)
        file_key = None
        is_bound = False

        try:
            uploaded_part_count = 0
            for upload_part in upload_parts:
                upload_response = file_api.upload_single_file_backend(
                    file_path=upload_part["file_path"],
                    file_name=upload_part["file_path"].name,
                    file_size=upload_part["file_size"],
                    entry_point=CT_ENTRY_POINT,
                    md5=upload_part["md5"],
                )
                assert_status_code_2xx(upload_response)
                upload_response_body = assert_response_json(upload_response)
                assert_business_code(upload_response_body, 0)
                uploaded_part_count += 1
            assert uploaded_part_count == len(upload_parts), (
                f"上传分片数量不符合预期，实际: {uploaded_part_count}，预期: {len(upload_parts)}"
            )

            create_response = file_api.start_file_upload(
                file_name=CT_FILE_NAME,
                entry_point=CT_ENTRY_POINT,
                frontend_oss_upload=True,
            )
            assert_status_code_2xx(create_response)
            create_response_body = assert_response_json(create_response)
            assert_business_code(create_response_body, 0)
            file_key = _extract_complete_file_key(create_response_body)

            bind_response = patient_api.bind_model_file_to_patient(
                patient_id=patient_id,
                file_key=file_key,
                tags=CT_BIND_TAGS,
                name="AP_wujia_CT",
                file_type=CT_BIND_TYPE,
                params=CT_BIND_PARAMS,
                jaw_type=CT_BIND_JAW_TYPE,
                treatment_id=CT_BIND_TREATMENT_ID,
            )
            assert_status_code_2xx(bind_response)
            bind_response_body = assert_response_json(bind_response)
            assert_business_code(bind_response_body, 0)
            is_bound = True

            detail_response = patient_api.search_patient_detail_v2(patient_id=patient_id)
            assert_status_code_2xx(detail_response)
            detail_response_body = assert_response_json(detail_response)
            assert_business_code(detail_response_body, 0)
            detail_data = detail_response_body.get("data")
            assert isinstance(detail_data, dict), f"查询患者详情响应 data 不是对象，响应: {detail_response_body}"
            detail_files = _extract_file_list(detail_data)
            assert _contains_file_key(detail_files or detail_data, file_key), (
                f"患者详情中未找到绑定的 CT fileKey={file_key}，响应: {detail_response_body}"
            )

            description_response = file_api.search_file_description([file_key])
            assert_status_code_2xx(description_response)
            description_response_body = assert_response_json(description_response)
            assert_business_code(description_response_body, 0)
            description = _extract_file_description(description_response_body, file_key)
            assert description is not None, f"文件描述响应中未找到 fileKey={file_key}，响应: {description_response_body}"
            assert _contains_file_key(description, file_key), (
                f"文件描述未包含目标 fileKey={file_key}，响应: {description_response_body}"
            )
        finally:
            if is_bound:
                pass
            #     _unbind_file_if_bound(patient_api, patient_id, file_key)
            # _delete_patient_if_created(patient_api, patient_id)
