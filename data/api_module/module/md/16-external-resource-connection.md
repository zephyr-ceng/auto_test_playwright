# 外部资源与连接

来源：`api-docs/api-build.md`
接口规范版本：`v1.0.0`
项目接口来源：`api-docs/apifox-collection.postman.json`

## 模块说明

预签名资源下载、网络探测、ROS WebSocket 和静态运行时资源。

## 接口总览

| 接口名称 | 请求方式 | 请求地址 | command | 是否鉴权 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `downloadChunks` | `GET` | `https://example-cdn.invalid/path/to/part` | - | 是 | `src/utils/chunkDownload.ts` |
| `loopWatchInternet` | `GET` | `{{internetPingUrl}}` | - | 是 | `src/layout/AdminLayout/components/SettingModal/components/Setting/hooks/useIntervalWifi.ts` |
| `ROSClient` | `GET` | `ws://localhost:9090` | - | 是 | `src/services/tower-ros/client.ts` |
| `fetchGdcmconvJs` | `GET` | `{{frontendBaseUrl}}/cs/gdcmconv.js` | - | 是 | `src/pages/SurgicalDesign/components/UploadModelFileFromLocalExploreModal/pipeline/worker/compressWorkerLogic.ts` |

## 接口明细

### 预签名分片下载

- 接口名称：`downloadChunks`
- 接口描述：从后端返回的 Part.DownloadURL 直接下载分片；URL 通常为 OSS/COS 预签名地址。
- 请求地址：`https://example-cdn.invalid/path/to/part`
- 本地解析地址：`https://example-cdn.invalid/path/to/part`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/utils/chunkDownload.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：无

#### 请求头

无

#### 请求体

无

#### 响应示例

`<Blob>`

### 网络在线探测

- 接口名称：`loopWatchInternet`
- 接口描述：默认探测公网 ping 地址判断网络连通性。
- 请求地址：`{{internetPingUrl}}`
- 本地解析地址：`https://tars.finetool.cn/ping`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/layout/AdminLayout/components/SettingModal/components/Setting/hooks/useIntervalWifi.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`internetPingUrl`

#### 请求头

无

#### 请求体

无

#### 响应示例

`HTTP 2xx/非 2xx`

### ROS Bridge WebSocket

- 接口名称：`ROSClient`
- 接口描述：通过 roslib 连接 ROS bridge，默认 ws://localhost:9090，可由界面输入 ws://{ip}:9090。
- 请求地址：`ws://localhost:9090`
- 本地解析地址：`ws://localhost:9090`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/services/tower-ros/client.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：无

#### 请求头

无

#### 请求体

无

#### 响应示例

`WebSocket messages`

### GDCM WASM 脚本

- 接口名称：`fetchGdcmconvJs`
- 接口描述：压缩 worker 加载公共静态脚本 /cs/gdcmconv.js。
- 请求地址：`{{frontendBaseUrl}}/cs/gdcmconv.js`
- 本地解析地址：`http://localhost:3000/cs/gdcmconv.js`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/pages/SurgicalDesign/components/UploadModelFileFromLocalExploreModal/pipeline/worker/compressWorkerLogic.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`frontendBaseUrl`

#### 请求头

无

#### 请求体

无

#### 响应示例

`JavaScript runtime`
