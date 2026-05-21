# 登录页用户协议自动化需求

## 1. 需求背景

对 `https://x.finetool.cn/login` 登录页的“阅读并同意用户协议”能力进行自动化覆盖，验证协议弹窗正文可读取且非空。后续实现需符合当前项目的 POM + pytest + Allure 分层架构：

`data/*.yaml -> pages/*_manager.py -> tests/test_*_page.py -> pytest assert -> core/conftest.py 截图 -> Allure report`

## 2. 测试对象

- 页面 URL：`/login`
- 页面标题：`Fyton`
- 页面名称：登录页
- 协议入口：登录表单中的“阅读并同意用户协议”
- 协议展示方式：点击“用户协议”文本后，在当前登录页打开标题为“用户协议”的弹窗

## 3. 建议改造范围

### 3.1 YAML 层

更新 `data/login_data.yaml`，新增协议相关定位器。建议保留现有登录定位器，并补充：

```yaml
agreement_checkbox_role: "checkbox"
agreement_checkbox_name: "阅读并同意用户协议"
agreement_text: "text=用户协议"
agreement_dialog: "[role='dialog']:has-text('用户协议')"
agreement_dialog_title: "[role='dialog'] h1:has-text('口腔种植导航系统用户协议')"
privacy_dialog_title: "[role='dialog'] h1:has-text('隐私保护协议')"
agreement_close_button: "[role='dialog'] button[aria-label='Close']"
```

说明：若后续页面增加独立链接或 `data-testid`，优先改用稳定 `data-testid`。

### 3.2 Page Object 层

更新 `pages/login_manager.py`，新增面向断言的业务方法，测试层不直接写选择器：

- 外部调用方法：`get_user_agreement_text() -> str`，打开登录页、点击协议入口、等待协议弹窗并返回协议正文。

返回值必须服务 pytest 断言，不在 Page Object 内做最终断言。

### 3.3 pytest 层

新增或更新 `tests/test_login_page.py`，只保留协议正文非空校验：

| 用例 ID | Allure story | 前置条件 | 操作 | 预期结果 |
| --- | --- | --- | --- | --- |
| LOGIN_AGREEMENT_001 | 用户协议内容校验 | 打开 `/login` | 点击“用户协议”，读取弹窗正文 | 协议正文 `strip()` 后不为空 |

## 4. Allure 要求

建议在测试类中使用：

- `@allure.feature("Login")`
- `@allure.story("用户协议内容校验")`

用例标题使用 `allure.dynamic.title(...)`，失败截图继续交由 `core/conftest.py` 处理。

## 5. 断言标准

自动化断言只聚焦协议正文可读取：

- 协议弹窗正文可被 Page Object 读取。
- 正文执行 `strip()` 后不为空。

## 6. 工具验证记录

- 使用 Playwright CLI 打开登录页，返回页面 URL `https://x.finetool.cn/login`，页面标题 `Fyton`。
- Playwright CLI 在本次环境中生成的快照文件为空，因此协议正文以 Browser 内置浏览器读取结果为准。
- 使用 Browser 内置浏览器打开登录页，DOM 中识别到：
  - `checkbox "阅读并同意用户协议" [checked]`
  - `generic: 阅读并同意用户协议`
  - 点击唯一的“用户协议”文本后出现 `dialog "用户协议"`。
- 协议弹窗正文已成功读取，正文约 2694 字符。

## 7. 风险与注意事项

- 当前登录页协议入口不是独立可见的 `a` 节点，后续自动化应避免依赖 DOM 层级过深的选择器。
- 协议内容属于产品合规文本，测试中只校验正文非空，不建议整篇全文硬编码。
- 登录页已有“账号密码登录”和“手机号登录”两个 tab，协议入口若在两个 tab 中复用，应按 tab 分别验证。
- 若未来协议弹窗改为新页面或新标签页，Page Object 方法应返回 URL 或弹窗状态，测试断言同步更新。
