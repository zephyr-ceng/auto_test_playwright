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

## 项目运转逻辑

整个项目的执行链路可以概括为：

`CSV/YAML 数据 -> pytest 用例 -> fixture -> BrowserManager -> Playwright page -> Page Object -> BasePage 方法 -> 页面结果 -> assert -> 失败截图/Allure`

### 1. page driver 获取：pytest fixture -> BrowserManager -> Playwright page

测试入口在 `tests/` 目录下的用例文件中。以登录和患者管理用例为例，fixture 会先创建 `Logger`，再实例化
`BrowserManager`，随后调用 `new_page()` 获取 Playwright 的 `page driver`。

这里的 `new_page()` 并不是单纯新开标签页，它会在浏览器尚未启动时自动触发 `start()`，完成
Playwright、browser、context 和 page 的初始化。拿到 `page` 之后，再把它注入 `LoginPage`、
`PatientsPage` 这类页面对象，供后续业务方法直接使用。测试结束后，fixture 统一调用 `manager.close()`
回收浏览器资源。

### 2. 方法实现：page object -> BasePage 公共能力 -> 业务方法封装

页面对象层位于 `pages/` 目录，`LoginPage`、`PatientsPage` 都继承自 `BasePage`。页面类自身负责从
YAML 文件中读取页面 `url` 和 `locator` 配置，把页面结构和业务动作绑定起来。

真正的通用操作能力由 `BasePage` 提供，例如 `open_url()`、`click()`、`type_text()`、
`click_by_text()`、`count_elements()`、`take_screenshot()` 等。页面对象不会直接在测试里散落定位和操作，
而是把这些基础动作组合成业务方法，例如登录页中的 `login_account()`，患者页中的
`create_patient_invalid()`、`create_patient_effective()`、`search_patient()`、
`count_page_patients()` 等。这样测试层调用的是“业务语义方法”，而不是零散的页面操作。

### 3. 断言判定：测试用例 -> 返回结果 -> assert 校验

测试层主要负责三件事：准备数据、调用页面方法、断言结果。数据通常来自 `CSVManager` 读取的 CSV，
页面定位和访问地址来自 YAML，因此测试用例本身保持较轻。

断言方式根据业务结果类型来决定：

- 登录失败场景中，`test_login_invalid()` 调用 `LoginPage.login_account()`，返回表单错误、toast 或弹窗文本，
  最终通过 `assert message == expected` 校验提示是否符合预期；
- 患者创建成功场景中，`test_create_patient_success()` 调用 `PatientsPage.create_patient_effective()`，
  返回当前页面 URL，再通过 `assert expected in url` 判断 URL 中是否包含 `patientID` 或 `createDesign`；
- 患者查询、方案查询、分页切换等场景中，页面方法返回布尔值或元素数量，测试再用 `assert res is True`
  或 `assert count == number` 进行判定。

### 辅助机制

除了主流程外，项目里还有两条关键的辅助链路：

- 登录态复用：`PatientsPage` 在打开业务页面前会调用 `LoginPage.refresh_cookies()`。这个方法会检查
  `config/config.yaml` 中缓存的 cookies 是否过期，如果过期就重新登录并写回配置，再通过
  `add_cookies()` 注入到当前浏览器上下文，保证需要登录态的页面可以直接访问。
- 失败截图与报告挂载：`core/conftest.py` 中的 `pytest_runtest_makereport` 会在测试执行失败时查找可截图对象，
  优先调用页面对象上的 `take_screenshot()`，若存在截图文件则继续尝试附加到 Allure 报告中，方便后续排查失败原因。

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
