# Playwright_demo

本项目是一个基于 **Playwright + Pytest** 的 Web 自动化测试示例工程，采用 **Page Object Model（POM）**
组织页面逻辑，用于验证系统中登录、患者管理等核心业务流程，并输出可视化测试报告。

## 项目作用

- 提供一套可复用的 UI 自动化测试框架模板；
- 将页面操作、测试数据、测试用例解耦，便于维护和扩展；
- 通过统一日志、失败截图和报告机制，提升问题定位效率。

## 实现效果

- 支持 **CSV 数据驱动** 执行测试用例；
- 已覆盖典型场景：
    - 登录失败提示校验；
    - 患者新建（成功/失败）校验；
    - 患者/方案查询；
    - 分页数量切换校验；
    - DICOM 文件渲染校验；
- 用例失败时自动截图，并可附加到 Allure 报告；
- 执行后可生成 Allure HTML 报告，直观查看通过率、失败详情和执行步骤。

## 技术栈

- Python 3.13+
- Playwright
- Pytest
- Allure
- PyYAML

## 目录说明（核心）

- `core/`：浏览器管理、pytest 钩子等基础能力；
- `pages/`：页面对象封装（页面定位与操作）；
- `tests/ui/`：UI 测试用例；
- `tests/api/`：requests 接口测试用例；
- `api/`：接口测试客户端、Apifox 生成器和模块 API 封装；
- `data/ui/`：UI 页面定位、规则说明和 UI 用例数据；
- `data/api/`：API 接口规格、模块文档和生成说明；
- `data/test_data/`：通用 CSV 测试数据；
- `data/dicom/`、`data/stl/`：UI 文件上传相关示例数据；
- `logs/`：运行日志与失败截图；
- `reports/`：测试结果与 Allure 报告输出；
- `run_tests.py`：按 UI/API suite 执行 pytest 并生成 Allure 报告。

## Codex Skill 使用

项目内已提供 `pom-pytest-allure` skill，用于把页面自动化需求转化为标准的 POM + YAML + Pytest + Allure
实现。后续向 Codex 提需求时，可以在开头写：

```text
使用 pom-pytest-allure：
```

Codex 会按以下约定生成或更新文件：

- `data/ui/<module>/<page>_page.yaml`：页面路径与元素定位，`url` 只写路径；
- `pages/<module>/<page>_manager.py`：页面对象封装，文件名必须使用 `*_manager.py`；
- `tests/ui/<module>/test_<page>_page.py`：pytest 用例、fixture、断言和 Allure 标记。

推荐需求模板：

```text
使用 pom-pytest-allure：

新增【页面/模块名称】自动化。

页面文件名：
<page>_manager.py

页面路径：
/path

环境前缀：
`config/config.yaml` 中的 `base_url`，页面 YAML 不写完整 URL。

测试流程：
1. 打开页面
2. 输入/选择/点击 ...
3. 触发业务操作
4. 获取页面结果

断言标准：
说明需要校验的实际结果和期望结果，例如：
- toast 文案等于「保存成功」
- 当前 URL 包含 patientID
- 表格至少存在 1 条数据
- 每条查询结果都包含输入关键字

元素定位：
- search_input: 输入框定位
- search_button: 查询按钮定位
- table_rows: 结果行定位
- toast_message: 提示信息定位

Allure 标记：
feature: <Feature 名称>
story: <Story 名称>
title: <用例标题规则>
```

## 快速运行

```bash
# 1) 安装依赖
pip install -r requirements.txt

# 2) 安装 Playwright 浏览器
python -m playwright install

# 3) 默认执行 UI 测试并生成 Allure 报告
python run_tests.py

# 只执行 API 安全冒烟集
python run_tests.py --suite api

# 执行 UI + API 安全冒烟集
python run_tests.py --suite all

# 调试时只跑 pytest，不生成 Allure HTML
python run_tests.py --suite api --no-allure-html
```

远程运行

- linux 执行 `playwright run-server --port 3000 --host 0.0.0.0`
- 配置 `/config/config.yaml` 的 `remote_url`

执行完成后，可在 `reports/html/` 查看生成的 Allure 报告。

## API 编写与调试

- 接口定义来源：`data/api/Tars Admin Frontend API.apifox.json`。
- 重新生成接口封装和测试：`python -m api.generate_from_apifox`。
- 生成结果：
    - `api/01-login_by_username-auth/api.py` 等 16 个目录：严格对齐 `api-test/cache/modules/01-...16-...`；
    - `tests/api/01-login_by_username-auth/test_01_login_auth_api.py` 等 16 个目录：对应 pytest + Allure 测试；
    - `config/environment.yaml`：Apifox/Postman 默认变量；
    - `api/generated/summary.json`：生成数量摘要；
    - `api/generated/unsupported_prerequest.md`：未支持前置脚本清单。
- 前置脚本处理在 `api/preprocessors.py`：依赖变量校验、CSV body patch、JSON body patch、随机患者名、form-data 文件检查。
- 默认 API suite 会跳过 `destructive_api` 和 `external_api`。调试单接口时可用：

```bash
python -m pytest tests/api/01-login_by_username-auth/test_01_login_auth_api.py -q -s
python -m pytest tests/api/02-patient-management/test_02_patient_management_api.py::TestPatientManagementApi::test_command_13001_2 -q -s
python -m pytest tests/api -q -m "destructive_api" -s
```

放开破坏性或外部依赖接口前，先确认 `config/environment.yaml` 的 API 地址和账号指向正确环境，并确认接口不会误删数据、控制设备或触发升级。
新增或调试接口时，先定位 `api-test/cache/modules/<编号>-<分组>.postman.json`，再查看同名目录下的 `api.py` 与
`test_<编号>_<分组>_api.py`。

## UI 编写与调试

- UI 用例统一放在 `tests/ui/<module>/`。
- 页面对象仍放在 `pages/<module>/*_manager.py`，定位数据放在 `data/ui/<module>/*_page.yaml`。
- 调试单个 UI 文件或用例：

```bash
python -m pytest tests/ui/login/test_login_page.py -q -s
python -m pytest tests/ui/patient_manager/test_patients_page.py::TestPatientsPage::test_create_patient_success -q -s
```

新增 UI 自动化时继续按 POM 结构编写：`data/ui/<module>/*_page.yaml -> pages/<module>/*_manager.py -> tests/ui/<module>/test_*_page.py`。失败截图仍由
`core/conftest.py` 统一处理。
