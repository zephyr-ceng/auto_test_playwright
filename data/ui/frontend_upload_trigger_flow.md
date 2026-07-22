# 前端文件上传触发流程

## CreateDesign 当前主流程

### 1. 全局上传监听挂载

入口文件：

- `src/layout/ConfigProvider/BaseScreen.tsx`

页面外层会调用：

```ts
useGlobalUpload();
```

这个 hook 会常驻监听上传 store 状态。

### 2. 用户选择或拖拽文件

入口组件：

- `src/v2/page/CreateDesign/compoment/treatmentPathway/UploadModelFileModalContent.tsx`

触发方式：

```text
点击上传按钮
拖拽文件到上传区域
```

之后进入：

```ts
parseFiles(files, isOnline);
```

### 3. 前端先本地解析文件

`parseFiles` 会根据文件类型走不同解析流程：

```text
.dcm / .dicom -> CT 解析 pipeline
.stl          -> STL 解析 pipeline
.ply          -> PLY 解析 pipeline
.partitionft  -> partitionft 解析 pipeline
.drc          -> DRC 解析 pipeline
```

解析成功后调用：

```ts
setUploadFile(targetFileData);
```

### 4. setUploadFile 不会立即上传

`setUploadFile` 的实现位置：

- `src/v2/page/CreateDesign/compoment/dataModal/index.tsx`

它主要做三件事：

```ts
curLoadFiles.current = file;
setFileType(file.fileType);
setModalType('crop');
```

也就是说，这一步只是把待上传文件暂存起来，并进入裁剪/确认导入界面。

### 5. 用户点击“确认导入”后才进入上传队列

确认逻辑在：

- `src/v2/page/CreateDesign/compoment/dataModal/index.tsx`

核心函数：

```ts
handleOK();
```

确认时会：

```text
校验备注
读取裁剪参数
读取当前模型显示参数
生成上传任务 id
写入上传队列 store
```

关键调用：

```ts
useModelDataStore.getState().pushUploadFileData(...);
```

### 6. store 写入 uploadFileData

store 定义位置：

- `src/store/modelDataSlice.ts`

关键方法：

```ts
pushUploadFileData: (data) => {
  state.uploadFileData = data;
};
```

这一步会更新：

```ts
uploadFileData;
```

### 7. useGlobalUpload 监听 uploadFileData

监听逻辑在：

- `src/v2/page/CreateDesign/compoment/dataModal/handlePiple.ts`

核心逻辑：

```ts
useEffect(() => {
  if (uploadFileData) {
    uploadManagement.current.addUploadFileData(uploadFileData);
  }
}, [uploadFileData]);
```

### 8. 上传管理器入队并启动上传

`addUploadFileData` 会把任务加入队列：

```ts
this.upLoadFileList.push(uploadFileData);
```

如果当前没有正在上传的任务，会调用：

```ts
this.startNextUpload();
```

随后进入：

```ts
this.pipelineUpload(nextUpload.files.files);
```

### 9. pipelineUpload 创建真正的上传流程

上传 pipeline 定义在：

- `src/v2/page/CreateDesign/compoment/dataModal/handlePiple.ts`

核心流程：

```text
LocalSource
  -> AddHeader
  -> ReadItkCTHeaderProcess
  -> Compress
  -> CombineWindow
  -> Encrypt
  -> UploadSink / UploadSinkOffline
```

其中：

```text
在线模式  -> UploadSink
离线模式  -> UploadSinkOffline
```

## 总体触发链路

```text
用户点击/拖拽文件
  -> parseFiles 本地解析
  -> setUploadFile 暂存文件
  -> 进入裁剪/确认界面
  -> 用户点击确认导入
  -> pushUploadFileData 写入 store
  -> useGlobalUpload 监听到 uploadFileData
  -> addUploadFileData 入队
  -> startNextUpload 启动队列任务
  -> pipelineUpload 执行上传 pipeline
  -> UploadSink / UploadSinkOffline 完成上传
```

## 旧 SurgicalDesign 流程

旧页面入口：

- `src/pages/SurgicalDesign/DesignLayout/Header.tsx`

这里传入的是：

```tsx
setUploadFile={startFileUpload}
```

`startFileUpload` 会直接调用：

```ts
pipelineUpload(file.file);
```

所以旧流程更短：

```text
用户选择/拖拽文件
  -> parseFiles 本地解析
  -> setUploadFile
  -> startFileUpload
  -> pipelineUpload
  -> UploadSink 上传
```

旧流程没有经过 CreateDesign 的全局上传队列，也不会走 `pushUploadFileData -> useGlobalUpload` 这条链路。
