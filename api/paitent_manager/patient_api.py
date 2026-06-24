from pathlib import Path

from requests import Response

from api.common.client import HTTPClient
from api.login_verification.login import Login


class PatientAPIS(Login):
    def __init__(self, client: HTTPClient):
        super().__init__(client)

    def add_patient(
            self,
            name: str,
            gender: int | None = None,
            date_of_birth: int | None = None,
            identity_card: str | None = None,
            telephone: str | None = None,
            desc: str | None = None,
    ) -> Response:
        """通过 gateway command 13002 新增患者，name 必填。"""
        payload: dict[str, str | int] = {"name": name}
        optional_fields: dict[str, str | int | None] = {
            "gender": gender,
            "dateOfBirth": date_of_birth,
            "identityCard": identity_card,
            "telephone": telephone,
            "desc": desc,
        }
        for key, value in optional_fields.items():
            if value is not None:
                payload[key] = value
        return self.client.send_request("POST", command="13002", json=payload)

    def update_patient(
            self,
            patient_id: str,
            name: str | None = None,
            gender: int | None = None,
            date_of_birth: int | None = None,
            identity_card: str | None = None,
            telephone: str | None = None,
            desc: str | None = None,
    ) -> Response:
        """通过 gateway command 13003 修改患者，patient_id 必填。"""
        payload: dict[str, str | int] = {"id": patient_id}
        optional_fields: dict[str, str | int | None] = {
            "name": name,
            "gender": gender,
            "dateOfBirth": date_of_birth,
            "identityCard": identity_card,
            "telephone": telephone,
            "desc": desc,
        }
        for key, value in optional_fields.items():
            if value is not None:
                payload[key] = value
        return self.client.send_request("POST", command="13003", json=payload)

    def query_patient_page(
            self,
            page_index: int,
            page_size: int,
            name: str | None = None,
            gender: int | None = None,
            telephone: str | None = None,
    ) -> Response:
        """通过 gateway command 13001 分页查询患者。"""
        payload: dict[str, str | int] = {
            "pageIndex": page_index,
            "pageSize": page_size,
        }
        optional_fields: dict[str, str | int | None] = {
            "name": name,
            "gender": gender,
            "telephone": telephone,
        }
        for key, value in optional_fields.items():
            if value is not None:
                payload[key] = value
        return self.client.send_request("POST", command="13001", json=payload)

    def delete_patient(self, patient_id: str) -> Response:
        """通过 gateway command 13004 删除患者，patient_id 必填。"""
        payload = {"id": patient_id}
        return self.client.send_request("POST", command="13004", json=payload)

    def query_patient_detail_v2(
            self,
            patient_id: str,
            need_files: bool = True,
            need_medical_records: bool = True,
    ) -> Response:
        """通过 gateway command 13007 查询患者详情 V2。"""
        payload: dict[str, str | bool] = {
            "id": patient_id,
            "needFiles": need_files,
            "needMedicalRecords": need_medical_records,
        }
        return self.client.send_request("POST", command="13007", json=payload)

    def start_file_upload(
            self,
            file_name: str,
            file_size: int,
            file_md5: str,
    ) -> Response:
        """通过 gateway command 11001 初始化附件分片上传。"""
        payload = {
            "entryPoint": 1,
            "fileName": file_name,
            "fileSize": file_size,
            "md5": file_md5,
            "frontendOssUpload": False,
            "partsInfo": [
                {
                    "partID": 1,
                    "partMD5": file_md5,
                    "partSize": file_size,
                }
            ],
            "extra": {
                "files": [
                    {
                        "filename": file_name,
                        "offset": 0,
                        "length": file_size,
                    }
                ],
                "compressVersion": 0,
                "cryptoVersion": 0,
            },
        }
        return self.client.send_request("POST", command="11001", json=payload)

    def upload_file_chunk(self, file_path: str | Path, file_key: str, part_id: int = 1) -> Response:
        """通过 /upload_part 上传单个附件分片。"""
        resolved_file_path = Path(file_path)
        with resolved_file_path.open("rb") as file_obj:
            files = {"content": (resolved_file_path.name, file_obj)}
            data = {
                "partID": str(part_id),
                "fileKey": file_key,
            }
            return self.client.send_request("POST", path="/upload_part", data=data, files=files)

    def finish_file_upload(self, file_key: str) -> Response:
        """通过 gateway command 11002 通知服务端附件上传完成。"""
        payload = {"fileKey": file_key}
        return self.client.send_request("POST", command="11002", json=payload)

    def bind_model_file_to_patient(
            self,
            patient_id: str,
            file_key: str,
            tags: list[str] | None = None,
            name: str | None = None,
            file_type: str | None = None,
            params: str | None = None,
            jaw_type: str | None = None,
    ) -> Response:
        """通过 gateway command 13005 将附件绑定到患者。"""
        payload: dict[str, object] = {
            "patientID": patient_id,
            "fileKey": file_key,
        }
        optional_fields: dict[str, object | None] = {
            "tags": tags,
            "name": name,
            "type": file_type,
            "params": params,
            "jawType": jaw_type,
        }
        for key, value in optional_fields.items():
            if value is not None:
                payload[key] = value
        return self.client.send_request("POST", command="13005", json=payload)

    def unbind_model_file_to_patient(self, patient_id: str, file_key: str) -> Response:
        """通过 gateway command 13006 解除患者与模型文件的绑定关系。"""
        payload = {
            "patientID": patient_id,
            "fileKey": file_key,
        }
        return self.client.send_request("POST", command="13006", json=payload)

    def change_bind_file(self, patient_id: str, old_file_key: str, new_file_key: str) -> Response:
        """通过 gateway command 13008 变更患者已绑定的模型文件。"""
        payload = {
            "patientID": patient_id,
            "oldFileKey": old_file_key,
            "newFileKey": new_file_key,
        }
        return self.client.send_request("POST", command="13008", json=payload)
