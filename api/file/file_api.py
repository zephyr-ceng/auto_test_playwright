from pathlib import Path

from requests import Response

from api.common.client import HTTPClient


class FileAPI:
    def __init__(self, client: HTTPClient) -> None:
        self.client = client

    def start_file_upload(
            self,
            file_name: str,
            entry_point: int,
            frontend_oss_upload: bool = True,
            file_size: int | None = None,
            md5: str | None = None,
            parts_info: list[dict] | None = None,
            extra: dict | None = None,
            parent_key: str | None = None,
    ) -> Response:
        """通过 gateway command 11001 开启完整文件上传会话。"""
        payload: dict = {
            "fileName": file_name,
            "entryPoint": entry_point,
            "frontendOssUpload": frontend_oss_upload,
        }
        optional_fields = {
            "fileSize": file_size,
            "md5": md5,
            "partsInfo": parts_info,
            "extra": extra,
            "parentKey": parent_key,
        }
        for key, value in optional_fields.items():
            if value is not None:
                payload[key] = value
        return self.client.send_request("POST", command="11001", json=payload)

    def upload_file_part_backend(self, file_path: str | Path, file_key: str, part_id: int = 1) -> Response:
        """通过 /upload_part 后端中转上传单个文件分片。"""
        resolved_file_path = Path(file_path)
        with resolved_file_path.open("rb") as file_obj:
            files = {"content": (resolved_file_path.name, file_obj)}
            data = {
                "partID": str(part_id),
                "fileKey": file_key,
            }
            return self.client.send_request("POST", path="/upload_part", data=data, files=files)

    def upload_single_file_backend(
            self,
            file_path: str | Path,
            file_name: str,
            file_size: int,
            entry_point: int,
            md5: str,
    ) -> Response:
        """通过 /upload 上传单个 DICOM 分片文件。"""
        resolved_file_path = Path(file_path)
        with resolved_file_path.open("rb") as file_obj:
            files = {"file": (resolved_file_path.name, file_obj)}
            data = {
                "fileName": file_name,
                "fileSize": str(file_size),
                "entryPoint": str(entry_point),
                "md5": md5,
            }
            return self.client.send_request("POST", path="/upload", data=data, files=files)

    def notify_file_chunk_upload_result(
            self,
            file_key: str,
            part_id: int,
            crypto_key: str,
            crypto_algo: int,
            size: int | None = None,
    ) -> Response:
        """通过 gateway command 11003 通知单个上传分片结果。"""
        payload: dict = {
            "fileKey": file_key,
            "partID": part_id,
            "cryptoKey": crypto_key,
            "cryptoAlgo": crypto_algo,
        }
        if size is not None:
            payload["size"] = size
        return self.client.send_request("POST", command="11003", json=payload)

    def finish_file_upload(
            self,
            file_key: str,
            extra: dict | None = None,
            size: int | None = None,
    ) -> Response:
        """通过 gateway command 11002 完成完整 CT 文件上传。"""
        payload: dict = {"fileKey": file_key}
        if extra is not None:
            payload["extra"] = extra
        if size is not None:
            payload["size"] = size
        return self.client.send_request("POST", command="11002", json=payload)

    def search_file_description(self, file_keys: list[str]) -> Response:
        """通过 gateway command 11004 查询文件分片与原文件描述。"""
        return self.client.send_request("POST", command="11004", json={"fileKeys": file_keys})
