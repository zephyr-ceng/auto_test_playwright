# 网络与 Wi-Fi

来源：`api-docs/api-build.md`
接口规范版本：`v1.0.0`
项目接口来源：`api-docs/apifox-collection.postman.json`

## 模块说明

网络速率、Wi-Fi 列表、连接状态和热点开关。

## 接口总览

| 接口名称 | 请求方式 | 请求地址 | command | 是否鉴权 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `getNetworkRealtimeRate` | `GET` | `{{controlNodeBaseUrl}}/network_status` | - | 是 | `src/api/network/index.ts` |
| `getWifiListAPI` | `GET` | `{{controlNodeBaseUrl}}/scan_wifi` | - | 是 | `src/api/wifi/index.ts` |
| `connectWifiAPI` | `POST` | `{{controlNodeBaseUrl}}/connect_wifi` | - | 是 | `src/api/wifi/index.ts` |
| `disConnectWifiAPI` | `POST` | `{{controlNodeBaseUrl}}/disconnect_wifi` | - | 是 | `src/api/wifi/index.ts` |
| `getAPListAPI` | `GET` | `{{controlNodeBaseUrl}}/ap_list` | - | 是 | `src/api/wifi/index.ts` |
| `OpenHotspotAPI` | `POST` | `{{controlNodeBaseUrl}}/open_hotspot` | - | 是 | `src/api/wifi/index.ts` |
| `closeHotspotAPI` | `POST` | `{{controlNodeBaseUrl}}/close_hotspot` | - | 是 | `src/api/wifi/index.ts` |

## 接口明细

### 获取网络实时速率

- 接口名称：`getNetworkRealtimeRate`
- 接口描述：查询有线/Wi-Fi/无网络状态及上下行速率。
- 请求地址：`{{controlNodeBaseUrl}}/network_status`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/network_status`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/api/network/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

无

#### 请求体

无

#### 响应示例


```json
{
  "code": 0,
  "data": {
    "networkType": "wifi",
    "downloadSpeed": 1024,
    "uploadSpeed": 512
  },
  "message": "success"
}
```

### 扫描 Wi-Fi 列表

- 接口名称：`getWifiListAPI`
- 接口描述：扫描可连接 Wi-Fi。
- 请求地址：`{{controlNodeBaseUrl}}/scan_wifi`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/scan_wifi`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/api/wifi/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

无

#### 请求体

无

#### 响应示例


```json
{
  "code": 0,
  "data": [
    {
      "key": "wifi-key",
      "ssid": "wifi-name",
      "signal": "-40",
      "security": "WPA2",
      "authRequired": true,
      "connected": false,
      "save": false
    }
  ],
  "message": "success"
}
```

### 连接 Wi-Fi

- 接口名称：`connectWifiAPI`
- 接口描述：按 ssid/password 连接 Wi-Fi。
- 请求地址：`{{controlNodeBaseUrl}}/connect_wifi`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/connect_wifi`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/wifi/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "ssid": "wifi-name",
  "password": "wifi-password",
  "save": true
}
```

#### 响应示例


```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

### 断开 Wi-Fi

- 接口名称：`disConnectWifiAPI`
- 接口描述：断开指定 Wi-Fi。
- 请求地址：`{{controlNodeBaseUrl}}/disconnect_wifi`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/disconnect_wifi`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/wifi/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "ssid": "wifi-name"
}
```

#### 响应示例


```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

### 获取热点列表

- 接口名称：`getAPListAPI`
- 接口描述：获取控制节点热点接口列表。
- 请求地址：`{{controlNodeBaseUrl}}/ap_list`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/ap_list`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/api/wifi/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

无

#### 请求体

无

#### 响应示例


```json
{
  "code": 0,
  "data": [
    {
      "iface": "wlan0",
      "hotspot_active": true,
      "ssid": "tars-hotspot",
      "password": "12345678",
      "auto_start": true
    }
  ],
  "message": "success"
}
```

### 开启热点

- 接口名称：`OpenHotspotAPI`
- 接口描述：开启指定网卡热点。
- 请求地址：`{{controlNodeBaseUrl}}/open_hotspot`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/open_hotspot`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/wifi/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "iface": "wlan0",
  "ssid": "tars-hotspot",
  "password": "12345678",
  "auto_start": true
}
```

#### 响应示例


```json
{
  "code": 0,
  "data": {
    "code": 0,
    "msg": "success",
    "data": null
  },
  "message": "success"
}
```

### 关闭热点

- 接口名称：`closeHotspotAPI`
- 接口描述：关闭指定网卡热点。
- 请求地址：`{{controlNodeBaseUrl}}/close_hotspot`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/close_hotspot`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/wifi/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "iface": "wlan0",
  "auto_start": false
}
```

#### 响应示例


```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```
