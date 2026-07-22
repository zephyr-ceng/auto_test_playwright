# 患者管理接口自动化改造说明

来源文档：`api/module/module/md/02-patient-management.md`

附件来源：`api-test/cache/modules/upload_attachment_to_patient.apifox.postman.json`

目标技能：`$api-pytest-builder`

目标架构：

```text
api/common/client.py
api/common/assertions.py
api/paitent_manager/patient_api.py
tests/api/single_api/test_patient_api.py
```

## 改造目标

将患者管理模块下的 gateway 接口和附件上传依赖接口改造为 requests + pytest 的 API 自动化结构。

要求：

- API 封装层只负责组装请求和发送请求，不做业务断言。
- pytest 用例层负责参数化、响应断言、前置数据准备和测试数据清理。
- 所有 gateway 接口统一通过 `HTTPClient.send_request("POST", command="<command>", json=payload)` 调用。
- `/upload_part` 普通路径接口统一通过 `HTTPClient.send_request("POST", path="/upload_part", data=data, files=files)` 调用。
- Cookie 鉴权由 `HTTPClient` 根据 `config/environment.yaml` 中的 `sessionCookie` 注入，业务 API 方法中不要手动传 Cookie。
- 请求字段保持后端 wire key 不变，例如 `dateOfBirth`、`identityCard`、`patientID`、`fileName`、`fileSize`。
- Python 方法参数使用 snake_case，例如 `date_of_birth`、`identity_card`、`patient_id`。
- 可选字段仅在参数值不是 `None` 时写入 payload，必须保留显式传入的空字符串。
- 测试数据中的姓名建议保留 `AP_` 前缀，便于识别自动化数据。
- 创建出来的临时患者必须在用例结束后删除，避免测试数据残留。

## 目标文件

API 封装文件：

```text
api/paitent_manager/patient_api.py
```

单接口测试文件：

```text
tests/api/single_api/test_patient_api.py
```

后续场景测试建议文件：

```text
tests/api/scenario/test_patient_lifecycle.py
```

## 公共测试准备

### 登录和客户端 Fixture

在患者单接口测试中保留或补充以下 fixture 职责：

- `auth_session_cookie`：session 级登录一次，写入或刷新 `sessionCookie`，供 gateway 接口复用。
- `http_client`：function 级创建 `HTTPClient`，测试结束后关闭 session。
- `patient_api`：function 级创建 `PatientAPIS` 实例，患者基础接口、附件上传接口和绑定接口统一从该实例调用。

### 患者 ID 提取

新增或保留私有辅助函数：

```text
_extract_patient_id(response_body)
```

职责：

- 从响应 `data` 中提取患者 ID。
- 兼容字段名：`id`、`ID`、`patientID`、`patientId`。
- 如果 `data` 不是对象或没有患者 ID，直接断言失败。

### 临时患者创建

新增或保留私有辅助函数：

```text
_create_patient_and_get_id(patient_api, patient_data=None)
```

职责：

- 调用新增患者接口准备前置数据。
- 只做前置数据准备所需的基础断言：HTTP 2xx、JSON、业务 code 为 0、能提取患者 ID。
- 返回 `patient_id`。

默认测试患者数据：

```json
{
  "name": "AP_<随机中文名>",
  "gender": 1,
  "date_of_birth": 631123200000,
  "telephone": "<随机手机号>"
}
```

### 临时患者清理

新增或保留私有辅助函数：

```text
_delete_patient_if_created(patient_api, patient_id)
```

职责：

- 如果 `patient_id` 为空，不执行删除。
- 如果 `patient_id` 存在，调用删除患者接口清理数据。
- 删除响应需要校验 HTTP 2xx、JSON、业务 code 为 0。

使用要求：

- `test_add_patient_success` 新增成功后在 `finally` 中删除患者。
- `test_update_patient_success` 前置创建的患者在 `finally` 中删除。
- `test_query_patient_page_success` 为筛选查询创建的患者在 `finally` 中删除。
- `test_query_patient_detail_v2_success` 前置创建的患者在 `finally` 中删除。
- 删除接口可作为清理能力保留，不建议在单接口层保留独立成功删除用例，完整删除链路后续放入场景测试。

### 附件上传准备

在 `PatientAPIS` 中新增或保留附件上传方法：

```text
start_file_upload
upload_file_chunk
finish_file_upload
```

职责：

- `start_file_upload`：通过 gateway command `11001` 初始化附件上传。
- `upload_file_chunk`：通过 `/upload_part` 上传单个附件分片，使用 `multipart/form-data`。
- `finish_file_upload`：通过 gateway command `11002` 通知服务端上传完成。

新增或保留私有辅助函数：

```text
_md5_file(file_path)
_upload_attachment_and_get_file_key(patient_api, file_path=DEFAULT_ATTACHMENT_PATH)
```

职责：

- 默认测试文件使用附件模块指定的 `data/dicom/wujia/SLZ+000.dcm`；如果本地项目已有稳定 DICOM 测试文件，也可以替换为仓库内存在的等价文件。
- 根据真实文件计算 `fileSize` 和 `fileMd5`，不要硬编码生产文件信息。
- 按附件顺序执行：初始化上传 -> 上传分片 -> 完成上传。
- 初始化上传响应需断言 `data.fileKey` 存在，并返回该 `fileKey` 供同一个 `patient_api.bind_model_file_to_patient` 使用。
- 如果测试文件不存在，使用 `pytest.skip` 明确跳过依赖附件文件的用例。

## 接口总览

| 原始接口名 | Python 方法名 | command | 是否需要登录 | 建议测试归属 |
| --- | --- | --- | --- | --- |
| `savePatient` | `add_patient` | `13002` | 是 | 单接口 |
| `updatePatient` | `update_patient` | `13003` | 是 | 单接口 |
| `queryPatientPage` | `query_patient_page` | `13001` | 是 | 单接口 |
| `delPatient` | `delete_patient` | `13004` | 是 | 清理能力/场景测试 |
| `startFileUpload` | `start_file_upload` | `11001` | 是 | 附件上传前置能力 |
| `uploadFileChunk` | `upload_file_chunk` | - | 是 | 附件上传前置能力 |
| `finishFileUpload` | `finish_file_upload` | `11002` | 是 | 附件上传前置能力 |
| `bindModelFileToPatient` | `bind_model_file_to_patient` | `13005` | 是 | 单接口，先上传附件获取 fileKey |
| `unbindModelFileToPatient` | `unbind_model_file_to_patient` | `13006` | 是 | 单接口，依赖绑定数据 |
| `searchPatientDetailsMessageV2` | `query_patient_detail_v2` | `13007` | 是 | 单接口 |
| `changeBindFile` | `change_bind_file` | `13008` | 是 | 单接口，依赖两个 fileKey |

## API 封装要求

### 1. 新增患者

原始接口：`savePatient`

Python 方法：

```text
add_patient(name, gender=None, date_of_birth=None, identity_card=None, telephone=None, desc=None)
```

请求：

- method：`POST`
- command：`13002`
- path：gateway，不传普通 path

字段映射：

| Python 参数 | 请求字段 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| `name` | `name` | 是 | 患者姓名 |
| `gender` | `gender` | 否 | 性别 |
| `date_of_birth` | `dateOfBirth` | 否 | 出生日期时间戳 |
| `identity_card` | `identityCard` | 否 | 身份证号，可传空字符串 |
| `telephone` | `telephone` | 否 | 手机号 |
| `desc` | `desc` | 否 | 备注，可传空字符串 |

成功响应断言：

- HTTP 状态码为 2xx。
- 响应体是 JSON 对象。
- `code == 0`。
- `data` 是对象。
- `data` 中包含患者 ID，兼容 `id`、`ID`、`patientID`、`patientId`。

建议单接口用例：

- 仅传 `name`。
- 传 `name + gender`。
- 传 `name + date_of_birth`。
- 传 `name + identity_card`，允许空字符串。
- 传 `name + telephone`。
- 传 `name + desc`，允许空字符串。
- 传全字段。
- `name` 为空时按当前接口实际行为断言，如果当前后端仍返回 `code == 0`，用例注释说明由前端做必填校验。

清理要求：

- 新增成功并提取到 `patient_id` 后，在 `finally` 中调用 `delete_patient` 删除。

### 2. 修改患者

原始接口：`updatePatient`

Python 方法：

```text
update_patient(patient_id, name=None, gender=None, date_of_birth=None, identity_card=None, telephone=None, desc=None)
```

请求：

- method：`POST`
- command：`13003`

字段映射：

| Python 参数 | 请求字段 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| `patient_id` | `id` | 是 | 患者 ID |
| `name` | `name` | 否 | 患者姓名 |
| `gender` | `gender` | 否 | 性别 |
| `date_of_birth` | `dateOfBirth` | 否 | 出生日期时间戳 |
| `identity_card` | `identityCard` | 否 | 身份证号，可传空字符串 |
| `telephone` | `telephone` | 否 | 手机号 |
| `desc` | `desc` | 否 | 备注 |

成功响应断言：

- HTTP 状态码为 2xx。
- 响应体是 JSON 对象。
- `code == 0`。

前置数据：

- 调用 `_create_patient_and_get_id` 创建临时患者。

建议单接口用例：

- 修改姓名。
- 修改性别。
- 修改出生日期。
- 修改手机号。
- 修改备注。
- 修改全字段。

清理要求：

- 修改接口用例结束后，在 `finally` 中调用 `delete_patient` 删除前置患者。

### 3. 分页查询患者

原始接口：`queryPatientPage`

Python 方法：

```text
query_patient_page(page_index, page_size, name=None, gender=None, telephone=None)
```

请求：

- method：`POST`
- command：`13001`

字段映射：

| Python 参数 | 请求字段 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| `page_index` | `pageIndex` | 是 | 页码 |
| `page_size` | `pageSize` | 是 | 每页条数 |
| `name` | `name` | 否 | 按姓名筛选 |
| `gender` | `gender` | 否 | 按性别筛选 |
| `telephone` | `telephone` | 否 | 按手机号筛选 |

成功响应断言：

- HTTP 状态码为 2xx。
- 响应体是 JSON 对象。
- `code == 0`。
- `data` 是对象。
- `data` 中包含列表字段，兼容 `data`、`list`、`records`。
- `data.total` 存在。

前置数据：

- 如果只验证分页结构，可以不创建患者。
- 如果验证筛选条件，应先创建姓名和手机号唯一的临时患者，再按姓名、性别、手机号查询。

建议单接口用例：

- 分页基础查询：`page_index=1`、`page_size=10`。
- 精确筛选查询：前置创建患者，按姓名、性别、手机号查询。

清理要求：

- 精确筛选查询创建的临时患者必须在 `finally` 中删除。

### 4. 删除患者

原始接口：`delPatient`

Python 方法：

```text
delete_patient(patient_id)
```

请求：

- method：`POST`
- command：`13004`

字段映射：

| Python 参数 | 请求字段 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| `patient_id` | `id` | 是 | 患者 ID |

成功响应断言：

- HTTP 状态码为 2xx。
- 响应体是 JSON 对象。
- `code == 0`。

测试策略：

- 单接口层优先将该接口作为临时数据清理能力。
- 不建议保留独立 `test_delete_patient_success`，避免删除测试与数据清理职责重复。
- 后续场景测试中可覆盖完整链路：新增患者 -> 查询患者 -> 修改患者 -> 删除患者 -> 再查询确认。

### 5. 初始化附件上传

原始接口：`startFileUpload`

Python 方法：

```text
start_file_upload(file_name, file_size, file_md5, part_id=1, entry_point=1, frontend_oss_upload=False)
```

请求：

- method：`POST`
- command：`11001`

字段映射：

| Python 参数 | 请求字段 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| `entry_point` | `entryPoint` | 否 | 上传入口，附件示例为 `1` |
| `file_name` | `fileName` | 是 | 文件名，附件示例为 `SLZ+000.dcm` |
| `file_size` | `fileSize` | 是 | 文件字节数，建议由本地文件读取 |
| `file_md5` | `md5` | 是 | 文件 MD5，建议由本地文件计算 |
| `frontend_oss_upload` | `frontendOssUpload` | 否 | 附件流程为 `false` |
| `part_id` | `partsInfo[].partID` | 否 | 单分片示例为 `1` |
| `file_md5` | `partsInfo[].partMD5` | 是 | 单分片 MD5，单分片时等于文件 MD5 |
| `file_size` | `partsInfo[].partSize` | 是 | 单分片大小，单分片时等于文件大小 |
| `file_name` | `extra.files[].filename` | 是 | `extra` 中的文件名 |
| `file_size` | `extra.files[].length` | 是 | `extra` 中的文件长度 |

成功响应断言：

- HTTP 状态码为 2xx。
- 响应体是 JSON 对象。
- `code == 0`。
- `data` 是对象。
- `data.fileKey` 存在且非空。

测试策略：

- 不建议作为患者单接口独立测试优先实现。
- 作为 `_upload_attachment_and_get_file_key` 的第一步，为绑定附件到患者提供真实 `fileKey`。

### 6. 上传附件分片

原始接口：`uploadFileChunk`

Python 方法：

```text
upload_file_chunk(file_path, file_key, part_id=1)
```

请求：

- method：`POST`
- path：`/upload_part`
- body：`multipart/form-data`

字段映射：

| Python 参数 | 请求字段 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| `part_id` | `partID` | 是 | 分片 ID，附件示例为 `1` |
| `file_path` | `content` | 是 | 上传文件对象，需与初始化上传的文件一致 |
| `file_key` | `fileKey` | 是 | 初始化上传返回的 `fileKey` |

成功响应断言：

- HTTP 状态码为 2xx。
- 响应体是 JSON 对象。
- `code == 0`。

实现要求：

- API 方法内使用 `Path(file_path).open("rb")` 构造 `files={"content": (文件名, file_obj)}`。
- 使用 `data={"partID": str(part_id), "fileKey": file_key}` 传普通表单字段。
- 不手动设置 `Content-Type`，让 `requests` 自动生成 multipart boundary。

### 7. 完成附件上传

原始接口：`finishFileUpload`

Python 方法：

```text
finish_file_upload(file_key)
```

请求：

- method：`POST`
- command：`11002`

字段映射：

| Python 参数 | 请求字段 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| `file_key` | `fileKey` | 是 | 初始化上传返回的文件 key |

成功响应断言：

- HTTP 状态码为 2xx。
- 响应体是 JSON 对象。
- `code == 0`。

测试策略：

- 作为 `_upload_attachment_and_get_file_key` 的最后一步。
- 完成上传后才将 `fileKey` 传给 `bind_model_file_to_patient`。

### 8. 绑定附件到患者

原始接口：`bindModelFileToPatient`

Python 方法：

```text
bind_model_file_to_patient(patient_id, file_key, tags=None, name=None, file_type=None, params=None, jaw_type=None)
```

请求：

- method：`POST`
- command：`13005`

字段映射：

| Python 参数 | 请求字段 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| `patient_id` | `patientID` | 是 | 患者 ID，注意字段是 `patientID` |
| `file_key` | `fileKey` | 是 | 文件 key |
| `tags` | `tags` | 否 | 标签数组，示例 `["ct"]` |
| `name` | `name` | 否 | 文件名，示例 `CT.dcm` |
| `file_type` | `type` | 否 | 文件类型，示例 `dcm` |
| `params` | `params` | 否 | 参数字符串，示例 `"{}"` |
| `jaw_type` | `jawType` | 否 | 颌位，示例 `upper` |

成功响应断言：

- HTTP 状态码为 2xx。
- 响应体是 JSON 对象。
- `code == 0`。
- `data` 是对象或空对象。

前置数据：

- 需要已有患者 ID。
- 需要先通过 `start_file_upload` -> `upload_file_chunk` -> `finish_file_upload` 获取可用 `fileKey`。
- 附件模块明确不要传 `treatmentID` 空字符串或 `0`，本接口封装不保留 `treatment_id` 参数。
- `tags`、`name`、`file_type`、`params`、`jaw_type` 按附件变量传入，示例：`["ct"]`、`SLZ+000.dcm`、`dcm`、`"{}"`、`upper`。

建议单接口用例：

- 创建临时患者。
- 上传附件并获取 `fileKey`。
- 绑定附件到患者。
- 可选：调用查询患者详情 V2，验证 `files` 中包含本次上传的 `fileKey`。

清理要求：

- 绑定成功后，优先调用 `unbind_model_file_to_patient` 解绑。
- 前置创建的临时患者在 `finally` 中删除。

### 9. 解绑患者模型文件

原始接口：`unbindModelFileToPatient`

Python 方法：

```text
unbind_model_file_to_patient(patient_id, file_key)
```

请求：

- method：`POST`
- command：`13006`

字段映射：

| Python 参数 | 请求字段 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| `patient_id` | `patientID` | 是 | 患者 ID |
| `file_key` | `fileKey` | 是 | 文件 key |

成功响应断言：

- HTTP 状态码为 2xx。
- 响应体是 JSON 对象。
- `code == 0`。
- `data` 是对象或空对象。

前置数据：

- 需要先完成患者与文件绑定。
- 可通过 `bind_model_file_to_patient` 做前置准备。

建议单接口用例：

- 先创建患者。
- 准备可用 `fileKey`。
- 调用绑定接口。
- 调用解绑接口并断言成功。

清理要求：

- 如果解绑失败，仍要尝试删除临时患者。
- 如绑定接口产生后端文件关系残留，应在 `finally` 中优先尝试解绑，再删除患者。

### 10. 查询患者详情 V2

原始接口：`searchPatientDetailsMessageV2`

Python 方法：

```text
query_patient_detail_v2(patient_id, need_files=True, need_medical_records=True)
```

请求：

- method：`POST`
- command：`13007`

字段映射：

| Python 参数 | 请求字段 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| `patient_id` | `id` | 是 | 患者 ID |
| `need_files` | `needFiles` | 否 | 是否返回文件信息，默认 `True` |
| `need_medical_records` | `needMedicalRecords` | 否 | 是否返回病历信息，默认 `True` |

成功响应断言：

- HTTP 状态码为 2xx。
- 响应体是 JSON 对象。
- `code == 0`。
- `data` 是对象。
- `data` 中包含患者 ID，兼容 `id`、`ID`、`patientID`、`patientId`。

前置数据：

- 调用 `_create_patient_and_get_id` 创建临时患者。

建议单接口用例：

- 默认参数查询：`need_files=True`、`need_medical_records=True`。
- 附件绑定验证查询：绑定附件后再次查询，断言 `data.files` 中存在本次上传的 `fileKey`。
- 可选参数关闭查询：`need_files=False`、`need_medical_records=False`，仅在后端支持时启用。

清理要求：

- 查询结束后，在 `finally` 中删除临时患者。

### 11. 变更绑定文件

原始接口：`changeBindFile`

Python 方法：

```text
change_bind_file(patient_id, old_file_key, new_file_key)
```

请求：

- method：`POST`
- command：`13008`

字段映射：

| Python 参数 | 请求字段 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| `patient_id` | `patientID` | 是 | 患者 ID |
| `old_file_key` | `oldFileKey` | 是 | 原文件 key |
| `new_file_key` | `newFileKey` | 是 | 新文件 key，来源变量名可对应原文档 `fileKey` |

成功响应断言：

- HTTP 状态码为 2xx。
- 响应体是 JSON 对象。
- `code == 0`。
- `data` 是对象或空对象。

前置数据：

- 需要已有患者 ID。
- 需要患者已绑定 `old_file_key`。
- 需要可用 `new_file_key`。
- `old_file_key` 和 `new_file_key` 可以分别通过附件上传链路生成；如果为了减少耗时使用环境固定值，必须在缺失时 `pytest.skip`，不要硬编码生产数据。

建议单接口用例：

- 创建患者。
- 上传或读取旧文件 key 并绑定旧文件。
- 上传或读取新文件 key。
- 调用变更绑定文件接口，将旧文件替换为新文件。
- 可选：查询详情确认文件信息变化，确认逻辑建议放到场景测试。

清理要求：

- 测试结束后尝试解绑当前绑定文件。
- 删除临时患者。

## 建议测试文件结构

### 单接口测试

文件：

```text
tests/api/single_api/test_patient_api.py
```

建议保留测试类：

```text
TestPatientAPI
```

建议用例：

| 用例名 | 测试目标 |
| --- | --- |
| `test_add_patient_success` | 新增患者成功，响应包含患者 ID |
| `test_update_patient_success` | 修改患者成功 |
| `test_query_patient_page_success` | 分页查询患者成功 |
| `test_query_patient_detail_v2_success` | 查询患者详情 V2 成功 |
| `test_bind_model_file_to_patient_success` | 上传附件并绑定到患者成功 |
| `test_unbind_model_file_to_patient_success` | 解绑模型文件成功，依赖绑定数据 |
| `test_change_bind_file_success` | 变更绑定文件成功，依赖两个文件 key |

说明：

- `delete_patient` 不单独作为成功删除用例优先实现，作为清理方法调用。
- 附件上传接口 `start_file_upload`、`upload_file_chunk`、`finish_file_upload` 作为绑定类用例的前置 helper 优先实现。
- 绑定附件到患者以附件为准，不传 `treatmentID`，也不要传空字符串或 `0`。
- 如果缺少本地 DICOM 测试文件，附件绑定、解绑、变更绑定用例应使用 `pytest.skip` 标记数据依赖未满足。

### 场景测试

文件：

```text
tests/api/scenario/test_patient_lifecycle.py
```

后续建议场景：

```text
新增患者 -> 分页查询 -> 查询详情 -> 修改患者 -> 再查详情 -> 删除患者
```

文件绑定场景：

```text
新增患者 -> 初始化附件上传 -> 上传附件分片 -> 完成附件上传 -> 绑定附件 -> 查询详情验证 files 包含 fileKey -> 解绑文件 -> 删除患者
```

## Allure 和 Pytest 标记

统一使用：

```text
@pytest.mark.api
@allure.feature("患者接口")
```

story 建议：

| 接口 | story |
| --- | --- |
| 新增患者 | `新增患者` |
| 修改患者 | `修改患者` |
| 分页查询患者 | `分页查询患者` |
| 查询患者详情 V2 | `查询患者详情` |
| 初始化附件上传 | `初始化附件上传` |
| 上传附件分片 | `上传附件分片` |
| 完成附件上传 | `完成附件上传` |
| 绑定模型文件 | `绑定附件到患者` |
| 解绑模型文件 | `解绑模型文件` |
| 变更绑定文件 | `变更绑定文件` |

## 验证命令

改造完成后至少执行：

```powershell
D:\ubuntu\Playwright_demo\.venv\Scripts\python.exe -m py_compile api/paitent_manager/patient_api.py tests/api/single_api/test_patient_api.py
D:\ubuntu\Playwright_demo\.venv\Scripts\python.exe -m pytest tests/api/single_api/test_patient_api.py -m api -q
```

如果文件相关接口因缺少稳定 DICOM 测试文件、`fileKey` 或 `oldFileKey` 暂时无法执行，需要在测试报告或提交说明中明确标注数据依赖未满足。
