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
- `tests/`：测试用例；
- `data/`：测试数据（含 YAML / DICOM 示例数据）；
- `logs/`：运行日志与失败截图；
- `reports/`：测试结果与 Allure 报告输出；
- `run_tests.py`：执行 pytest 并生成 Allure 报告。

## Codex Skill 使用

项目内已提供 `pom-pytest-allure` skill，用于把页面自动化需求转化为标准的 POM + YAML + Pytest + Allure
实现。后续向 Codex 提需求时，可以在开头写：

```text
使用 pom-pytest-allure：
```

Codex 会按以下约定生成或更新文件：

- `data/<page>_page.yaml`：页面路径与元素定位，`url` 只写路径；
- `pages/<page>_manager.py`：页面对象封装，文件名必须使用 `*_manager.py`；
- `tests/test_<page>_page.py`：pytest 用例、fixture、断言和 Allure 标记。

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

# 3) 执行测试并生成 Allure 报告
python run_tests.py
```

执行完成后，可在 `reports/html/` 查看生成的 Allure 报告。
