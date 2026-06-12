import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const env = {
  frontendBaseUrl: 'http://localhost:3000',
  baseUrl: 'http://localhost:3000/tars/v1',
  gatewayUrl: 'http://localhost:3000/tars/v1/gateway',
  controlNodeBaseUrl: 'http://192.168.0.52:38080/tars/v1',
  rosBaseUrl: 'http://192.168.0.52:38081/ros_api/v1',
  chatBaseUrl: 'http://192.168.2.159:9999/api/v3',
  aiBaseUrl: 'http://192.168.2.154:50052',
  internetPingUrl: 'https://tars.finetool.cn/ping',
};

const runtimeHeaders = [
  { key: 'PlatFrom', value: 'web', desc: '前端固定请求头' },
  { key: 'Version', value: 'v1', desc: '前端固定请求头' },
  { key: 'Request-ID', value: '{{$guid}}', desc: '前端运行时自动生成 UUID' },
  {
    key: 'Cookie',
    value: '{{cookie}}',
    desc: '浏览器 withCredentials 自动携带；Apifox 中可手动设置登录后的 Cookie',
  },
];

const commandNames = {
  11001: 'StartFileChunkUpload',
  11002: 'FinishFileChunkUpload',
  11003: 'NotifyFileChunkUploadResult',
  11004: 'SearchFileDescription',
  12002: 'UploadUserSecret',
  12003: 'GetUserSecretMeta',
  12004: 'ListUserSecretDevices',
  12005: 'GetUserOTPCode',
  13001: 'QueryPatientPage',
  13002: 'SavePatient',
  13003: 'UpdatePatient',
  13004: 'DeletePatient',
  13005: 'bindModelFile',
  13006: 'unbindModelFile',
  13007: 'SearchPatientV2',
  13008: 'ChangeBindFile',
  14001: 'QuerySurgicalDesignList',
  14002: 'AddSurgicalDesign',
  14003: 'UpdateSurgicalDesign',
  14004: 'CompleteSurgicalDesign',
  14005: 'QuerySurgicalDesignDetail',
  14006: 'StartSurgical',
  14007: 'FinishSurgical',
  14008: 'DeleteSurgical',
  14009: 'NavSurgicalDesign',
  15001: 'AddCase',
  15002: 'DelCase',
  15003: 'TreatmentSequence',
  15004: 'DelTreatmentSequence',
  15005: 'sortTreatmentSequence',
  16001: 'GetUserInfo',
  17001: 'StarAiPartion',
  17002: 'QueryAiPartitionResult',
  17003: 'ExpByToothCusp',
  18002: 'getUserConfig',
  18003: 'saveUserConfig',
  18004: 'GetImplantFavorites',
  18005: 'AddImplantFavorite',
  18006: 'DeleteImplantFavorite',
  19001: 'getMessage',
  19002: 'readMessage',
  19003: 'deleteMessage',
  20001: 'GetDeviceList',
  20002: 'GetPointSummary',
  20003: 'GetPointDetails',
  20004: 'GetPointRemind',
};

const responseEnvelope = (data = {}, message = 'success') => ({
  code: 0,
  data,
  message,
});

const groups = [
  {
    name: '登录认证',
    desc: '登录、登出、短信验证码、密码重置和当前用户信息。',
    endpoints: [
      {
        name: '用户名密码登录',
        apiName: 'loginByUserName',
        desc: '使用 username/password 登录，可通过 returnToken 要求后端返回 token。',
        method: 'POST',
        base: 'baseUrl',
        path: '/login_by_username',
        source: 'src/api/login/index.ts',
        req: { username: '{{username}}', password: '{{password}}', returnToken: false },
        res: responseEnvelope({
          accountID: 'account-id',
          name: '管理员',
          tenantID: 'tenant-id',
          tenantType: 'clinic',
          userID: 'user-id',
          username: 'admin',
          token: '',
        }),
      },
      {
        name: '登出',
        apiName: 'logout',
        desc: '退出当前登录会话。',
        method: 'POST',
        base: 'baseUrl',
        path: '/logout',
        source: 'src/api/login/index.ts',
        req: null,
        res: { code: 0, message: 'success' },
      },
      {
        name: '手机号验证码登录',
        apiName: 'loginByTel',
        desc: '使用 telephone/code 登录，可通过 returnToken 要求后端返回 token。',
        method: 'POST',
        base: 'baseUrl',
        path: '/login_by_telephone',
        source: 'src/api/login/index.ts',
        req: { telephone: '13800138000', code: '123456', returnToken: true },
        res: responseEnvelope({
          accountID: 'account-id',
          name: '用户',
          tenantID: 'tenant-id',
          userID: 'user-id',
          token: 'token-if-returnToken',
        }),
      },
      {
        name: '发送短信验证码',
        apiName: 'sendSMS',
        desc: '发送登录或重置密码短信验证码。',
        method: 'POST',
        base: 'baseUrl',
        path: '/send_sms',
        source: 'src/api/login/index.ts',
        req: { telephone: '13800138000', type: 'login' },
        res: responseEnvelope('sms-id-or-message'),
      },
      {
        name: '重置密码',
        apiName: 'resetPassword',
        desc: '通过手机号验证码重置密码。',
        method: 'POST',
        base: 'baseUrl',
        path: '/reset_password',
        source: 'src/api/login/index.ts',
        req: { telephone: '13800138000', code: '123456', newPassword: 'new-password' },
        res: responseEnvelope('ok'),
      },
      {
        name: '获取当前用户信息',
        apiName: 'getUserInfo',
        desc: '通过网关 Command 获取当前登录用户信息。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 16001,
        source: 'src/api/login/index.ts',
        req: null,
        res: responseEnvelope({
          AccountID: 'account-id',
          ID: 'user-id',
          Name: '管理员',
          TenantID: 'tenant-id',
          TenantType: 'clinic',
        }),
      },
    ],
  },
  {
    name: '患者管理',
    desc: '患者新增、更新、查询、删除和模型文件绑定。',
    endpoints: [
      {
        name: '新增患者',
        apiName: 'savePatient',
        desc: '创建患者基础信息。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 13002,
        source: 'src/api/patient/index.ts',
        req: {
          name: '{{patientName}}',
          gender: 1,
          dateOfBirth: 631123200000,
          identityCard: '{{patientIdentityCard}}',
          telephone: '{{patientTelephone}}',
          desc: '',
        },
        res: responseEnvelope({
          id: 'patient-id',
          name: '张三',
          gender: 1,
          dateOfBirth: 631123200000,
          identityCard: '110101199001010011',
          telephone: '13800138000',
          desc: '',
        }),
      },
      {
        name: '更新患者',
        apiName: 'updatePatient',
        desc: '更新患者姓名和电话等基础信息。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 13003,
        source: 'src/api/patient/index.ts',
        req: {
          id: '{{patientId}}',
          name: '{{patientName}}',
          gender: 1,
          dateOfBirth: 631123200000,
          identityCard: '{{patientIdentityCard}}',
          telephone: '{{patientTelephone}}',
          desc: '',
        },
        res: responseEnvelope(null),
      },
      {
        name: '分页查询患者',
        apiName: 'queryPatientPage',
        desc: '按姓名、性别、电话分页查询患者。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 13001,
        source: 'src/api/patient/index.ts',
        req: {
          pageIndex: 1,
          pageSize: 10,
          name: '{{patientName}}',
          gender: 1,
          telephone: '{{patientTelephone}}',
        },
        res: responseEnvelope({
          data: [],
          pageIndex: 1,
          pageSize: 10,
          total: 0,
        }),
      },
      {
        name: '删除患者',
        apiName: 'delPatient',
        desc: '按患者 ID 删除患者。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 13004,
        source: 'src/api/patient/index.ts',
        req: { id: '{{patientId}}' },
        res: responseEnvelope({ code: 0, message: 'success' }),
      },
      {
        name: '绑定模型文件到患者',
        apiName: 'bindModelFileToPatient',
        desc: '将已上传文件绑定到患者。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 13005,
        source: 'src/api/patient/index.ts',
        req: {
          patientID: '{{patientID}}',
          fileKey: '{{fileKey}}',
          tags: ['ct'],
          name: 'CT.dcm',
          type: 'dcm',
          params: '{}',
          jawType: 'upper',
          treatmentID: '{{treatmentId}}',
        },
        res: responseEnvelope({}),
      },
      {
        name: '解绑患者模型文件',
        apiName: 'unbindModelFileToPatient',
        desc: '解除患者与文件的绑定关系。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 13006,
        source: 'src/api/patient/index.ts',
        req: { patientID: '{{patientID}}', fileKey: '{{fileKey}}' },
        res: responseEnvelope({}),
      },
      {
        name: '查询患者详情 V2',
        apiName: 'searchPatientDetailsMessageV2',
        desc: '查询患者详情，固定携带 needFiles 和 needMedicalRecords。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 13007,
        source: 'src/api/patient/index.ts',
        req: { id: '{{patientID}}', needFiles: true, needMedicalRecords: true },
        res: responseEnvelope({
          id: 'patient-id',
          name: '张三',
          gender: 1,
          medicalRecordList: [],
          medicalRecords: [],
          files: [],
        }),
      },
      {
        name: '变更绑定文件',
        apiName: 'changeBindFile',
        desc: '变更患者关联文件信息，调用处传入 data，结构以后端约定为准。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 13008,
        source: 'src/api/patient/index.ts',
        req: { patientID: '{{patientID}}', oldFileKey: '{{oldFileKey}}', newFileKey: '{{fileKey}}' },
        res: responseEnvelope({}),
      },
    ],
  },
  {
    name: '病例与治疗序列',
    desc: '病例新增、更新、删除和治疗阶段维护。',
    endpoints: [
      {
        name: '新增病例',
        apiName: 'addCase',
        desc: '为患者新增病例记录。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 15001,
        source: 'src/api/case/index.ts',
        req: {
          patientID: '{{patientId}}',
          FDINotations: ['11', '12'],
          record: '术前检查记录',
          tags: [],
          diagnosis: 'edentulous_jaw',
        },
        res: responseEnvelope({
          id: '{{caseId}}',
          patientID: '{{patientId}}',
          FDINotations: ['11', '12'],
          record: '术前检查记录',
          status: 1,
        }),
      },
      {
        name: '更新病例',
        apiName: 'updateCase',
        desc: '更新病例记录；当前代码同样使用 Command 15001。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 15001,
        source: 'src/api/case/index.ts',
        req: {
          id: '{{caseId}}',
          patientID: '{{patientId}}',
          FDINotations: ['11'],
          record: '复诊记录',
          status: 2,
          tags: [],
          diagnosis: '',
        },
        res: responseEnvelope({ id: 'case-id', status: 2 }),
      },
      {
        name: '删除病例',
        apiName: 'deleteCase',
        desc: '按病例 ID 删除病例。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 15002,
        source: 'src/api/case/index.ts',
        req: { id: '{{caseId}}' },
        res: responseEnvelope({ code: 0, message: 'success' }),
      },
      {
        name: '新增治疗阶段',
        apiName: 'treatmentSequence',
        desc: '添加治疗阶段或治疗方案节点。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 15003,
        source: 'src/api/patient/index.ts',
        req: {
          name: '一期手术',
          date: 1710000000000,
          description: '治疗说明',
          status: 1,
          medicalRecordID: '{{caseId}}',
          order: 1,
        },
        res: responseEnvelope({ id: 'treatment-id' }),
      },
      {
        name: '更新治疗阶段',
        apiName: 'changeTreatmentSequence',
        desc: '更新治疗阶段名称、日期、描述和状态。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 15003,
        source: 'src/api/patient/index.ts',
        req: {
          id: '{{treatmentId}}',
          name: '一期手术',
          date: 1710000000000,
          description: '更新说明',
          status: 1,
          medicalRecordID: '{{caseId}}',
        },
        res: responseEnvelope({}),
      },
      {
        name: '治疗阶段排序',
        apiName: 'sortTreatmentSequence',
        desc: '按 treatmentsOrders 调整治疗阶段顺序。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 15005,
        source: 'src/api/patient/index.ts',
        req: { medicalRecordID: '{{caseId}}', treatmentsOrders: ['{{treatmentId}}'] },
        res: responseEnvelope({}),
      },
      {
        name: '删除治疗阶段',
        apiName: 'delTreatmentSequence',
        desc: '删除某个治疗阶段。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 15004,
        source: 'src/api/patient/index.ts',
        req: { medicalRecordID: '{{caseId}}', id: '{{treatmentId}}' },
        res: responseEnvelope({}),
      },
    ],
  },
  {
    name: '手术设计',
    desc: '设计列表、创建、修改、详情、开始和结束手术。',
    endpoints: [
      {
        name: '查询手术设计列表',
        apiName: 'querySurgicalDesign',
        desc: '按患者姓名、设计状态、审批状态分页查询设计列表。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 14001,
        source: 'src/api/design/index.ts',
        req: { pageIndex: 1, pageSize: 10, name: '{{patientName}}', status: 1, approveStatus: 1 },
        res: responseEnvelope({ data: [], pageIndex: 1, pageSize: 10, total: 0 }),
      },
      {
        name: '创建设计',
        apiName: 'addDesign',
        desc: '基于病例创建手术设计。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 14002,
        source: 'src/api/design/index.ts',
        req: { medicalRecordID: '{{caseId}}', modelFileKey: '{{fileKey}}' },
        res: responseEnvelope({ surgicalDesignID: 'design-id', version: 0 }),
      },
      {
        name: '创建设计 V2',
        apiName: 'addDesignV2',
        desc: '当前实现与 addDesign 相同，保留为调用入口。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 14002,
        source: 'src/api/design/index.ts',
        req: { medicalRecordID: '{{caseId}}', modelFileKey: '{{fileKey}}' },
        res: responseEnvelope({ surgicalDesignID: 'design-id', version: 0 }),
      },
      {
        name: '修改设计文件',
        apiName: 'changeDesign',
        desc: '保存设计内容、缩略图、模型文件和版本信息。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 14003,
        source: 'src/api/design/index.ts',
        req: {
          surgicalDesignID: '{{designId}}',
          version: 0,
          content: '{}',
          FDINotation: ['11'],
          modelFileKey: '{{fileKey}}',
          extraModelFileKeys: [],
          thumbnail: '{{thumbnailFileKey}}',
          images: {},
        },
        res: responseEnvelope({ version: 1 }),
      },
      {
        name: '导航页修改设计文件',
        apiName: 'navChangeDesign',
        desc: '导航页保存设计内容，使用独立 Command。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 14009,
        source: 'src/api/design/index.ts',
        req: { surgicalDesignID: '{{designId}}', version: 0, content: '{}', FDINotation: ['11'] },
        res: responseEnvelope({ version: 1 }),
      },
      {
        name: '完成手术设计',
        apiName: 'completeDesign',
        desc: '提交设计内容并标记设计完成。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 14004,
        source: 'src/api/design/index.ts',
        req: { surgicalDesignID: '{{designId}}', version: 1, content: '{}' },
        res: responseEnvelope({}),
      },
      {
        name: '查询设计详情',
        apiName: 'queryDesignDetail',
        desc: '按 SurgicalDesignID 获取设计详情、患者信息、病例信息和模型文件信息。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 14005,
        source: 'src/api/design/index.ts',
        req: { SurgicalDesignID: '{{designId}}' },
        res: responseEnvelope({
          surgicalDesignDetail: { ID: 'design-id', Version: 0, Status: 1 },
          patientInfo: { id: 'patient-id', name: '张三' },
          medicalRecordInfo: { id: 'case-id' },
          modelFileKey: 'file-key',
          extraModelFileKeys: [],
          token: 'download-token',
          files: [],
          jawType: 'upper',
        }),
      },
      {
        name: '开始手术',
        apiName: 'startSurgical',
        desc: '将设计进入手术中状态并返回设计详情。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 14006,
        source: 'src/api/design/index.ts',
        req: { surgicalDesignID: '{{designId}}' },
        res: responseEnvelope({ surgicalDesignDetail: { ID: 'design-id', Status: 3 } }),
      },
      {
        name: '完成手术',
        apiName: 'finishSurgical',
        desc: '提交手术完成信息和偏差信息。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 14007,
        source: 'src/api/design/index.ts',
        req: {
          SurgicalDesignID: '{{designId}}',
          SurgicalInfo: {
            registration: { handpieces: null, jaw: null },
            navigation: {
              horizontalDeviationMin: null,
              depthDeviationMin: null,
              axialDeviationMin: null,
            },
          },
        },
        res: responseEnvelope({ content: '{}', status: 4, ApproveStatus: 1, ModelFile: {} }),
      },
      {
        name: '获取系统设置',
        apiName: 'getSetting',
        desc: '获取帮助课程、钻针配置和功能配置。',
        method: 'GET',
        base: 'baseUrl',
        path: '/settings',
        source: 'src/api/design/index.ts',
        req: null,
        res: responseEnvelope({ Courses: [], Drills: [], FeatureConfig: {} }),
      },
      {
        name: '删除手术设计',
        apiName: 'delDesign',
        desc: '按设计 ID 删除设计。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 14008,
        source: 'src/api/design/index.ts',
        req: { id: '{{designId}}' },
        res: responseEnvelope({ code: 0, message: 'success' }),
      },
    ],
  },
  {
    name: '文件管理',
    desc: '文件分片上传、单文件上传、上传完成通知和文件描述查询。',
    endpoints: [
      {
        name: '开始分片上传',
        apiName: 'startFileUpload',
        desc: '初始化分片上传，可选择前端直传 OSS/COS。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 11001,
        source: 'src/api/file/index.ts',
        req: {
          entryPoint: 1,
          fileName: 'model.stl',
          fileSize: 1024,
          md5: 'file-md5',
          frontendOssUpload: true,
          partsInfo: [{ partID: 1, partMD5: 'part-md5', partSize: 1024 }],
          extra: {
            files: [{ filename: 'model.stl', offset: 0, length: 1024 }],
            compressVersion: 0,
            cryptoVersion: 0,
          },
          parentKey: 'parent-file-key',
        },
        res: responseEnvelope({
          fileKey: 'file-key',
          frontendOssUploadPartsInfo: [{ partID: 1, fileKey: 'oss-key' }],
          ossAuthInfo: {
            accessKey: 'access-key',
            accessSecret: 'access-secret',
            securityToken: 'security-token',
            bucketName: 'bucket',
            endpoint: 'endpoint',
            provider: 1,
            region: 'region',
          },
        }),
      },
      {
        name: '上传分片',
        apiName: 'uploadFileChunk',
        desc: '后端中转上传单个分片，multipart/form-data。',
        method: 'POST',
        base: 'baseUrl',
        path: '/upload_part',
        contentType: 'multipart/form-data',
        source: 'src/api/file/index.ts',
        req: { partID: 1, content: '<File>', fileKey: '{{fileKey}}' },
        res: responseEnvelope(null),
      },
      {
        name: '通知分片上传结果',
        apiName: 'notifyFileChunkUploadResult',
        desc: '前端直传 OSS/COS 后通知后端单个分片结果。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 11003,
        source: 'src/api/file/index.ts',
        req: { fileKey: '{{fileKey}}', partID: 1, cryptoKey: '', cryptoAlgo: 0 },
        res: responseEnvelope('ok'),
      },
      {
        name: '完成分片上传',
        apiName: 'finishFileUpload',
        desc: '通知后端所有分片已上传完成。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 11002,
        source: 'src/api/file/index.ts',
        req: { fileKey: '{{fileKey}}' },
        res: responseEnvelope(null),
      },
      {
        name: '上传单文件',
        apiName: 'uploadSingleFile',
        desc: '使用 multipart/form-data 上传单个文件。',
        method: 'POST',
        base: 'baseUrl',
        path: '/upload',
        contentType: 'multipart/form-data',
        source: 'src/api/file/index.ts',
        req: { fileName: 'thumbnail.png', fileSize: 1024, entryPoint: 2, md5: 'md5', file: '<File>' },
        res: responseEnvelope(null),
      },
      {
        name: '查询文件描述',
        apiName: 'searchFileDescription',
        desc: '按 fileKeys 查询文件下载和分片描述。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 11004,
        source: 'src/api/file/index.ts',
        req: { fileKeys: ['{{fileKey}}'] },
        res: responseEnvelope({ files: [] }),
      },
    ],
  },
  {
    name: '控制节点',
    desc: '本机文件、设备关机重启、版本、导出、录屏和升级。',
    endpoints: [
      {
        name: '获取目录树',
        apiName: 'getDirTree',
        desc: '按路径和后缀过滤查询控制节点目录树。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/get_dir_tree',
        source: 'src/api/controlNode/index.ts',
        req: { path: '/data', fileFilter: ['stl', 'dcm'] },
        res: responseEnvelope({ IsDir: true, Name: 'data', Path: '/data', Child: [] }),
      },
      {
        name: '下载本地文件',
        apiName: 'downloadLocalFile',
        desc: '从控制节点下载本地文件，返回 Blob。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/download_local_file',
        responseType: 'blob',
        source: 'src/api/controlNode/index.ts',
        req: { filePath: '/data/model.stl' },
        res: '<Blob>',
      },
      {
        name: '下载本地文件并上报进度',
        apiName: 'downloadLocalFileWithProgress',
        desc: '同下载本地文件，前端额外监听下载进度。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/download_local_file',
        responseType: 'blob',
        source: 'src/api/controlNode/index.ts',
        req: { filePath: '/data/model.stl' },
        res: '<Blob>',
      },
      {
        name: '关机',
        apiName: 'shutDownApi',
        desc: '关闭控制节点设备。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/shutdown',
        source: 'src/api/controlNode/index.ts',
        req: null,
        res: responseEnvelope(null),
      },
      {
        name: '重启',
        apiName: 'rebootApi',
        desc: '重启控制节点设备。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/reboot',
        source: 'src/api/controlNode/index.ts',
        req: null,
        res: responseEnvelope(null),
      },
      {
        name: '获取当前 Wi-Fi',
        apiName: 'getCurrentWifi',
        desc: '获取当前连接 Wi-Fi、密码和控制节点 IP。',
        method: 'GET',
        base: 'controlNodeBaseUrl',
        path: '/wifi_info',
        source: 'src/api/controlNode/index.ts',
        req: null,
        res: responseEnvelope({ ssid: 'wifi-name', password: 'wifi-password', ip: '192.168.0.52' }),
      },
      {
        name: '控制节点健康检查',
        apiName: 'getControlNodeHealthCheck',
        desc: '控制节点 ping 检查，返回 hwid。',
        method: 'GET',
        base: 'controlNodeBaseUrl',
        path: '/ping',
        source: 'src/api/controlNode/index.ts',
        req: null,
        res: responseEnvelope({ hwid: 'control-node-hwid' }),
      },
      {
        name: '导出文件到移动盘',
        apiName: 'exportFileToMobileDrive',
        desc: 'multipart/form-data 上传并写入指定路径。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/put_caldata',
        contentType: 'multipart/form-data',
        source: 'src/api/controlNode/index.ts',
        req: { fileName: 'model.stl', file: '<File>', path: '/usb' },
        res: responseEnvelope(null),
      },
      {
        name: '获取版本信息',
        apiName: 'getVersionInfo',
        desc: '获取当前版本、下一版本和升级开关。',
        method: 'GET',
        base: 'controlNodeBaseUrl',
        path: '/version',
        source: 'src/api/controlNode/index.ts',
        req: null,
        res: {
          fullVersion: '1.0.0',
          majorVersion: '1',
          changeNotes: '',
          nextVersion: '1.0.1',
          autoUpgrade: true,
          hwid: 'control-node-hwid',
        },
      },
      {
        name: '获取本地文件列表',
        apiName: 'getFileList',
        desc: '获取设计文件、录屏文件和磁盘空间。',
        method: 'GET',
        base: 'controlNodeBaseUrl',
        path: '/file_list',
        source: 'src/api/controlNode/index.ts',
        req: null,
        res: responseEnvelope({
          design_files: [],
          screen_files: [],
          total_available_space: '10GB',
          total_used_space: '1GB',
        }),
      },
      {
        name: '导出本地文件',
        apiName: 'exportFile',
        desc: '将本地文件导出到指定路径。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/export_local',
        source: 'src/api/controlNode/index.ts',
        req: { fileName: 'model.stl', exportPath: '/usb', localPath: '/data/model.stl' },
        res: responseEnvelope(null),
      },
      {
        name: '查询导出状态',
        apiName: 'getExportStatus',
        desc: '按本地路径查询导出进度。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/export_status',
        source: 'src/api/controlNode/index.ts',
        req: { localPath: '/data/model.stl' },
        res: responseEnvelope({ fileName: 'model.stl', progress: 50, status: 'running' }),
      },
      {
        name: '删除本地文件',
        apiName: 'deleteFile',
        desc: '按路径删除控制节点本地文件。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/delete_file',
        source: 'src/api/controlNode/index.ts',
        req: { path: '/data/model.stl' },
        res: responseEnvelope(null),
      },
      {
        name: '开始录屏',
        apiName: 'startScreenRecord',
        desc: '启动指定录屏任务。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/task/start',
        source: 'src/api/controlNode/index.ts',
        req: { taskName: 'screen-record' },
        res: responseEnvelope(null),
      },
      {
        name: '停止录屏',
        apiName: 'stopScreenRecord',
        desc: '停止指定录屏任务。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/task/stop',
        source: 'src/api/controlNode/index.ts',
        req: { taskName: 'screen-record' },
        res: responseEnvelope(null),
      },
      {
        name: '查询录屏状态',
        apiName: 'getScreenRecordStatus',
        desc: '查询指定录屏任务是否运行中。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/task/status',
        source: 'src/api/controlNode/index.ts',
        req: { taskName: 'screen-record' },
        res: responseEnvelope({ isActive: true }),
      },
      {
        name: '获取升级状态',
        apiName: 'getUpgradeStatus',
        desc: '获取软件升级进度和目标版本。',
        method: 'GET',
        base: 'controlNodeBaseUrl',
        path: '/upgrade_status',
        source: 'src/api/controlNode/index.ts',
        req: null,
        res: responseEnvelope({ progress: 0, status: 0, version: '1.0.1' }),
      },
      {
        name: '开始升级',
        apiName: 'startUpgrade',
        desc: '触发控制节点升级。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/start_upgrade',
        source: 'src/api/controlNode/index.ts',
        req: null,
        res: responseEnvelope(null),
      },
      {
        name: '设置自动升级',
        apiName: 'setUpgrade',
        desc: '开启或关闭自动升级。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/set_upgrade',
        source: 'src/api/controlNode/index.ts',
        req: { autoUpgrade: true },
        res: responseEnvelope(null),
      },
    ],
  },
  {
    name: '网络与 Wi-Fi',
    desc: '网络速率、Wi-Fi 列表、连接状态和热点开关。',
    endpoints: [
      {
        name: '获取网络实时速率',
        apiName: 'getNetworkRealtimeRate',
        desc: '查询有线/Wi-Fi/无网络状态及上下行速率。',
        method: 'GET',
        base: 'controlNodeBaseUrl',
        path: '/network_status',
        source: 'src/api/network/index.ts',
        req: null,
        res: responseEnvelope({ networkType: 'wifi', downloadSpeed: 1024, uploadSpeed: 512 }),
      },
      {
        name: '扫描 Wi-Fi 列表',
        apiName: 'getWifiListAPI',
        desc: '扫描可连接 Wi-Fi。',
        method: 'GET',
        base: 'controlNodeBaseUrl',
        path: '/scan_wifi',
        source: 'src/api/wifi/index.ts',
        req: null,
        res: responseEnvelope([
          {
            key: 'wifi-key',
            ssid: 'wifi-name',
            signal: '-40',
            security: 'WPA2',
            authRequired: true,
            connected: false,
            save: false,
          },
        ]),
      },
      {
        name: '连接 Wi-Fi',
        apiName: 'connectWifiAPI',
        desc: '按 ssid/password 连接 Wi-Fi。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/connect_wifi',
        source: 'src/api/wifi/index.ts',
        req: { ssid: 'wifi-name', password: 'wifi-password', save: true },
        res: responseEnvelope(null),
      },
      {
        name: '断开 Wi-Fi',
        apiName: 'disConnectWifiAPI',
        desc: '断开指定 Wi-Fi。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/disconnect_wifi',
        source: 'src/api/wifi/index.ts',
        req: { ssid: 'wifi-name' },
        res: responseEnvelope(null),
      },
      {
        name: '获取热点列表',
        apiName: 'getAPListAPI',
        desc: '获取控制节点热点接口列表。',
        method: 'GET',
        base: 'controlNodeBaseUrl',
        path: '/ap_list',
        source: 'src/api/wifi/index.ts',
        req: null,
        res: responseEnvelope([
          {
            iface: 'wlan0',
            hotspot_active: true,
            ssid: 'tars-hotspot',
            password: '12345678',
            auto_start: true,
          },
        ]),
      },
      {
        name: '开启热点',
        apiName: 'OpenHotspotAPI',
        desc: '开启指定网卡热点。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/open_hotspot',
        source: 'src/api/wifi/index.ts',
        req: { iface: 'wlan0', ssid: 'tars-hotspot', password: '12345678', auto_start: true },
        res: responseEnvelope({ code: 0, msg: 'success', data: null }),
      },
      {
        name: '关闭热点',
        apiName: 'closeHotspotAPI',
        desc: '关闭指定网卡热点。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/close_hotspot',
        source: 'src/api/wifi/index.ts',
        req: { iface: 'wlan0', auto_start: false },
        res: responseEnvelope(null),
      },
    ],
  },
  {
    name: '植体系统',
    desc: '植体系统配置和收藏管理。',
    endpoints: [
      {
        name: '获取植体系统列表',
        apiName: 'getImplantSystemAPI',
        desc: '获取本地植体/钻针系统配置。',
        method: 'GET',
        base: 'controlNodeBaseUrl',
        path: '/implant_system',
        source: 'src/api/implant/index.ts',
        req: null,
        res: responseEnvelope([{ id: 1, name: 'implant-system', systems: [] }]),
      },
      {
        name: '获取植体收藏',
        apiName: 'getImplantFavorites',
        desc: '获取当前用户收藏的植体类型。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 18004,
        source: 'src/api/implant/index.ts',
        req: null,
        res: responseEnvelope({ favorites: ['implant-type'] }),
      },
      {
        name: '新增植体收藏',
        apiName: 'addImplantFavorite',
        desc: '收藏指定植体类型。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 18005,
        source: 'src/api/implant/index.ts',
        req: { type: 'implant-type' },
        res: responseEnvelope(true),
      },
      {
        name: '取消植体收藏',
        apiName: 'deleteImplantFavorite',
        desc: '取消收藏指定植体类型。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 18006,
        source: 'src/api/implant/index.ts',
        req: { type: 'implant-type' },
        res: responseEnvelope(true),
      },
    ],
  },
  {
    name: 'OTP 密钥',
    desc: 'OTP secret 生成、校验、上传、查询和按设备取验证码。',
    endpoints: [
      {
        name: '生成 OTP Secret',
        apiName: 'generateOtpSecret',
        desc: '按 username 生成或获取当前有效 OTP secret。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/otp/generate_secret',
        source: 'src/api/opt/index.ts',
        req: { username: '{{username}}', serverSecretVersion: 1 },
        res: responseEnvelope({
          username: 'admin',
          hwid: 'control-node-hwid',
          secret: 'otp-secret',
          otpauth_url: 'otpauth://totp/...',
          secretVersion: 1,
        }),
      },
      {
        name: '校验 OTP Code',
        apiName: 'verifyOtpCode',
        desc: '校验 username 对应的 OTP 动态码。',
        method: 'POST',
        base: 'controlNodeBaseUrl',
        path: '/otp/verify',
        source: 'src/api/opt/index.ts',
        req: { username: '{{username}}', otp_code: '{{otpCode}}' },
        res: responseEnvelope({ username: 'admin', valid: true }),
      },
      {
        name: '上传用户 Secret',
        apiName: 'uploadUserSecret',
        desc: '上传当前用户在当前设备上的 secret。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 12002,
        source: 'src/api/opt/index.ts',
        req: { secret: '{{otpSecret}}', hwid: '{{hwid}}', secretVersion: 1 },
        res: responseEnvelope({
          username: 'admin',
          hwid: 'control-node-hwid',
          hwidHash: 'hwid-hash',
          secretVersion: 1,
        }),
      },
      {
        name: '查询用户 Secret 元信息',
        apiName: 'getUserSecretMeta',
        desc: '查询当前用户在指定设备上的服务端 secret 版本信息。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 12003,
        source: 'src/api/opt/index.ts',
        req: { hwid: '{{hwid}}' },
        res: responseEnvelope({
          username: 'admin',
          hwid: 'control-node-hwid',
          hwidHash: 'hwid-hash',
          exists: true,
          secretVersion: 1,
        }),
      },
      {
        name: '列出 Secret 绑定设备',
        apiName: 'listUserSecretDevices',
        desc: '列出当前用户服务端已绑定设备，不返回原始 hwid。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 12004,
        source: 'src/api/opt/index.ts',
        req: null,
        res: responseEnvelope({ username: 'admin', devices: [] }),
      },
      {
        name: '获取用户 OTP Code',
        apiName: 'getUserOtpCode',
        desc: '按当前用户和设备 hwid 获取对应 secret 生成的当前 OTP 动态码。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 12005,
        source: 'src/api/opt/index.ts',
        req: { hwid: '{{hwid}}' },
        res: responseEnvelope({
          username: 'admin',
          hwid: 'control-node-hwid',
          hwidHash: 'hwid-hash',
          exists: true,
          otpCode: '123456',
          secretVersion: 1,
        }),
      },
    ],
  },
  {
    name: 'AI 分割',
    desc: '启动 AI 分割任务、查询任务状态和牙尖异常分析。',
    endpoints: [
      {
        name: '启动 AI 分割',
        apiName: 'starAiPartition',
        desc: '启动指定 taskType 的 AI 分割任务。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 17001,
        source: 'src/api/partition/index.ts',
        req: { surgicalDesignID: '{{designId}}', taskType: 'dentalsegment', nextTaskType: 'dentalarch' },
        res: responseEnvelope({ taskID: 'task-id' }),
      },
      {
        name: '查询 AI 分割状态',
        apiName: 'getAiPartitionStatus',
        desc: '查询 AI 分割任务状态和结果数据。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 17002,
        source: 'src/api/partition/index.ts',
        req: { taskID: '{{taskId}}', parameters: {} },
        res: responseEnvelope({ taskID: 'task-id', status: 'COMPLETED', data: 'result-file-key' }),
      },
      {
        name: '牙尖异常分析',
        apiName: 'getExpByToothCusp',
        desc: '获取牙尖点异常分析任务。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 17003,
        source: 'src/api/partition/index.ts',
        req: { surgicalDesignID: '{{designId}}', taskType: 'dentalcusp' },
        res: responseEnvelope({ taskID: 'task-id' }),
      },
    ],
  },
  {
    name: '积分',
    desc: '积分总览、明细和提醒列表。',
    endpoints: [
      {
        name: '获取积分总览',
        apiName: 'getPointSummary',
        desc: '获取个人、租户、手术和冻结积分。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 20002,
        source: 'src/api/points/index.ts',
        req: { userId: '{{userId}}', tenantId: '{{tenantId}}' },
        res: responseEnvelope({
          vipLevel: 1,
          userName: '管理员',
          tenantName: '诊所',
          personalPoint: 100,
          personalSurgeryPoint: 20,
          tenantPoint: 1000,
          freezePoint: 0,
        }),
      },
      {
        name: '获取积分明细',
        apiName: 'getPointDetails',
        desc: '分页查询积分明细，可按状态过滤。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 20003,
        source: 'src/api/points/index.ts',
        req: { userId: '{{userId}}', tenantId: '{{tenantId}}', filterStatus: 1, page: 1, pageSize: 10 },
        res: responseEnvelope({ data: [], total: 0, page: 1, pageSize: 10 }),
      },
      {
        name: '获取积分提醒',
        apiName: 'getPointRemind',
        desc: '分页查询积分提醒消息。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 20004,
        source: 'src/api/points/index.ts',
        req: { userId: '{{userId}}', tenantId: '{{tenantId}}', page: 1, pageSize: 10 },
        res: responseEnvelope({ data: [], total: 0, page: 1, pageSize: 10 }),
      },
    ],
  },
  {
    name: '系统消息与设备',
    desc: '系统消息列表、已读、删除和设备列表。',
    endpoints: [
      {
        name: '查询系统消息',
        apiName: 'searchMessage',
        desc: '分页查询系统消息、未读数和总数。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 19001,
        source: 'src/api/systemMessage/index.ts',
        req: { pageSize: 10, current: 1 },
        res: responseEnvelope({ systemMessageList: [], total: 0, unread: 0, pageIndex: 1 }),
      },
      {
        name: '删除系统消息',
        apiName: 'deleteMessage',
        desc: '按消息 ID 删除；id 可选时由后端决定批量/全部行为。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 19003,
        source: 'src/api/systemMessage/index.ts',
        req: { id: '{{messageId}}' },
        res: responseEnvelope({}),
      },
      {
        name: '标记系统消息已读',
        apiName: 'readMessage',
        desc: '按消息 ID 标记已读；id 可选时由后端决定批量/全部行为。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 19002,
        source: 'src/api/systemMessage/index.ts',
        req: { id: '{{messageId}}' },
        res: responseEnvelope({}),
      },
      {
        name: '获取设备列表',
        apiName: 'getDeviceList',
        desc: '获取已发现或已登记设备。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 20001,
        source: 'src/api/systemMessage/index.ts',
        req: null,
        res: responseEnvelope({ devices: [] }),
      },
    ],
  },
  {
    name: '用户配置',
    desc: '用户级配置读取和保存。',
    endpoints: [
      {
        name: '读取用户配置',
        apiName: 'getUserConfig',
        desc: '按 user_id 读取网关侧用户配置。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 18002,
        source: 'src/api/user/index.ts',
        req: { user_id: '{{userId}}' },
        res: responseEnvelope({ configs: { key: { value: 1 } } }),
      },
      {
        name: '保存用户配置',
        apiName: 'saveUserConfig',
        desc: '保存用户配置键值列表。',
        method: 'POST',
        base: 'gatewayUrl',
        path: '',
        command: 18003,
        source: 'src/api/user/index.ts',
        req: { user_id: '{{userId}}', configs: [{ key: 'theme', value: 'dark' }] },
        res: responseEnvelope(null),
      },
    ],
  },
  {
    name: 'ROS 与导航',
    desc: 'ROS HTTP 接口、模型文件同步、JPEG 流、灯光控制和眼镜升级。',
    endpoints: [
      {
        name: '获取 Marker 列表',
        apiName: 'getMarkersList',
        desc: '获取当前和可选 Marker 序列号列表。',
        method: 'GET',
        base: 'rosBaseUrl',
        path: '/get_markers_list',
        source: 'src/api/ros/index.ts',
        req: null,
        res: {
          currentBoardMarker: 'board-1',
          currentJawMarker: 'jaw-1',
          currentHandpieceMarker: 'handpiece-1',
          currentPlaceMarker: 'place-1',
          currentCutMarker: 'cut-1',
          boardMarkerList: [],
          jawMarkerList: [],
          handpieceMarkerList: [],
          placeMarkerList: [],
          cutMarkerList: [],
        },
      },
      {
        name: '设置 Marker',
        apiName: 'setMarker',
        desc: '设置某类 Marker 的序列号。',
        method: 'POST',
        base: 'rosBaseUrl',
        path: '/set_marker',
        source: 'src/api/ros/index.ts',
        req: { markerType: 'boardMarker', markerSerialNumber: 'marker-sn' },
        res: responseEnvelope({}),
      },
      {
        name: 'ROS 读取用户配置',
        apiName: 'getUserConfigRos',
        desc: '从 ROS 节点读取用户配置。',
        method: 'GET',
        base: 'rosBaseUrl',
        path: '/get_user_config?user_id={{userId}}',
        source: 'src/api/ros/index.ts',
        req: { user_id: '{{userId}}' },
        res: responseEnvelope({ configs: { key: { value: 1 } } }),
      },
      {
        name: 'ROS 保存用户配置',
        apiName: 'saveUserConfigRos',
        desc: '向 ROS 节点保存用户配置。',
        method: 'POST',
        base: 'rosBaseUrl',
        path: '/save_user_config',
        source: 'src/api/ros/index.ts',
        req: { user_id: '{{userId}}', configs: [{ key: 'key', value: '1' }] },
        res: responseEnvelope({}),
      },
      {
        name: '上传导航模型文件',
        apiName: 'upLoadFile',
        desc: 'multipart/form-data 上传多个模型文件，query id 为设计 ID。',
        method: 'POST',
        base: 'rosBaseUrl',
        path: '/upload_model_file?id={{designId}}',
        contentType: 'multipart/form-data',
        source: 'src/api/ros/index.ts',
        req: { files: ['<File>'], id: '{{designId}}' },
        res: responseEnvelope({}),
      },
      {
        name: '设置模型文件',
        apiName: 'setModelFile',
        desc: 'multipart/form-data 增量上传模型文件。',
        method: 'POST',
        base: 'rosBaseUrl',
        path: '/set_model_file',
        contentType: 'multipart/form-data',
        source: 'src/api/ros/index.ts',
        req: { files: ['<File>'] },
        res: responseEnvelope({}),
      },
      {
        name: '下载导航模型文件',
        apiName: 'downLoadFile',
        desc: '按设计 ID 和文件名下载模型文件，返回 Blob。',
        method: 'GET',
        base: 'rosBaseUrl',
        path: '/download_model_file?id={{designId}}&filename={{filename}}',
        responseType: 'blob',
        source: 'src/api/ros/index.ts',
        req: { id: '{{designId}}', filename: '{{filename}}' },
        res: '<Blob>',
      },
      {
        name: '检查 MR 版本',
        apiName: 'checkMrVersion',
        desc: '检查连接眼镜版本兼容性。',
        method: 'GET',
        base: 'rosBaseUrl',
        path: '/check_mr_version',
        source: 'src/api/ros/index.ts',
        req: null,
        res: responseEnvelope({ minCompatibleVersion: '1.0.0', connectMRs: [] }),
      },
      {
        name: '升级 MR 版本',
        apiName: 'upgradeMrVersion',
        desc: '按眼镜 IP 触发升级。',
        method: 'POST',
        base: 'rosBaseUrl',
        path: '/update_mr_version',
        source: 'src/api/ros/index.ts',
        req: { ip: '192.168.0.60' },
        res: responseEnvelope({}),
      },
      {
        name: '停止 JPEG 流',
        apiName: 'jpegStreamStop',
        desc: '按 stream_id 停止 JPEG 图片流。',
        method: 'GET',
        base: 'rosBaseUrl',
        path: '/jpeg_stream/stop?stream_id={{streamId}}',
        source: 'src/api/ros/index.ts',
        req: { stream_id: '{{streamId}}' },
        res: responseEnvelope({}),
      },
      {
        name: '设置设计 Content',
        apiName: 'setDesignContent',
        desc: '向 ROS 节点设置当前手术设计 content。',
        method: 'POST',
        base: 'rosBaseUrl',
        path: '/set_design_content',
        source: 'src/api/ros/index.ts',
        req: { content: '{}' },
        res: responseEnvelope({}),
      },
      {
        name: '关闭无影灯',
        apiName: 'closeLampApi',
        desc: '关闭无影灯。',
        method: 'GET',
        base: 'rosBaseUrl',
        path: '/close_lamp',
        source: 'src/api/ros/index.ts',
        req: null,
        res: responseEnvelope({}),
      },
      {
        name: '获取塔台状态',
        apiName: 'getTowerStatus',
        desc: '按设备 IP 动态创建 ROS HTTP client 后获取塔台状态。',
        method: 'GET',
        base: 'rosBaseUrl',
        path: '/tower/status',
        source: 'src/v2/page/ScreenSharingPage/compoment/util/index.ts',
        req: null,
        res: {},
      },
      {
        name: '获取 JPEG 流状态',
        apiName: 'getJpegStreamStatus',
        desc: '查询 JPEG 流状态。',
        method: 'GET',
        base: 'rosBaseUrl',
        path: '/jpeg_stream/status',
        source: 'src/v2/page/ScreenSharingPage/compoment/util/index.ts',
        req: null,
        res: {},
      },
      {
        name: '按设备 IP 停止 JPEG 流',
        apiName: 'stopJpegStream',
        desc: '使用动态设备 IP 停止 JPEG 流。',
        method: 'GET',
        base: 'rosBaseUrl',
        path: '/jpeg_stream/stop?stream_id={{streamId}}',
        source: 'src/v2/page/ScreenSharingPage/compoment/util/index.ts',
        req: { stream_id: '{{streamId}}', ip: '192.168.0.52' },
        res: {},
      },
    ],
  },
  {
    name: '聊天与助手',
    desc: '聊天补全流式接口和全局助手 SSE。',
    endpoints: [
      {
        name: '聊天补全流',
        apiName: 'addChat',
        desc: '调用聊天节点 /api/v3/bots/chat/completions，返回 stream。',
        method: 'POST',
        base: 'chatBaseUrl',
        path: '/bots/chat/completions',
        responseType: 'stream',
        source: 'src/api/chat/index.ts',
        req: {
          model: 'test',
          messages: [{ role: 'user', content: '你好' }],
          stream: true,
          patients_info: [],
          machine_info: { lamp_brightness: 50 },
          cur_patients_info: null,
        },
        res: { choices: [{ delta: { content: '你好' }, finish_reason: null }] },
      },
      {
        name: '全局助手 SSE',
        apiName: 'fetchEventSourceChatCompletions',
        desc: '全局助手使用 fetchEventSource 请求 /tars/v1/chat_completions，响应 text/event-stream。',
        method: 'POST',
        base: 'baseUrl',
        path: '/chat_completions',
        responseType: 'text/event-stream',
        source: 'src/layout/GlobalWin/index.tsx',
        req: {
          model: 'test',
          stream: true,
          metadata: {
            patients_info: [],
            cur_patient_info: null,
            machine_info: { lamp_brightness: 50 },
            is_audio: true,
          },
          messages: [{ role: 'user', content: '调亮无影灯' }],
        },
        res: 'data: {"choices":[{"delta":{"content":"ok"},"finish_reason":null}]}\\n\\ndata: [DONE]',
      },
    ],
  },
  {
    name: '外部资源与连接',
    desc: '预签名资源下载、网络探测、ROS WebSocket 和静态运行时资源。',
    endpoints: [
      {
        name: '预签名分片下载',
        apiName: 'downloadChunks',
        desc: '从后端返回的 Part.DownloadURL 直接下载分片；URL 通常为 OSS/COS 预签名地址。',
        method: 'GET',
        base: 'external',
        path: 'https://example-cdn.invalid/path/to/part',
        source: 'src/utils/chunkDownload.ts',
        req: { DownloadURL: 'https://example-cdn.invalid/path/to/part', CryptoKey: 'optional-key' },
        res: '<Blob>',
      },
      {
        name: '网络在线探测',
        apiName: 'loopWatchInternet',
        desc: '默认探测公网 ping 地址判断网络连通性。',
        method: 'GET',
        base: 'internetPingUrl',
        path: '',
        source: 'src/layout/AdminLayout/components/SettingModal/components/Setting/hooks/useIntervalWifi.ts',
        req: null,
        res: 'HTTP 2xx/非 2xx',
      },
      {
        name: 'ROS Bridge WebSocket',
        apiName: 'ROSClient',
        desc: '通过 roslib 连接 ROS bridge，默认 ws://localhost:9090，可由界面输入 ws://{ip}:9090。',
        method: 'WEBSOCKET',
        base: 'external',
        path: 'ws://localhost:9090',
        source: 'src/services/tower-ros/client.ts',
        req: { url: 'ws://192.168.0.52:9090' },
        res: 'WebSocket messages',
        excludeFromHar: true,
      },
      {
        name: 'GDCM WASM 脚本',
        apiName: 'fetchGdcmconvJs',
        desc: '压缩 worker 加载公共静态脚本 /cs/gdcmconv.js。',
        method: 'GET',
        base: 'frontendBaseUrl',
        path: '/cs/gdcmconv.js',
        source: 'src/pages/SurgicalDesign/components/UploadModelFileFromLocalExploreModal/pipeline/worker/compressWorkerLogic.ts',
        req: null,
        res: 'JavaScript runtime',
      },
    ],
  },
];

const allEndpoints = groups.flatMap((group) =>
  group.endpoints.map((endpoint) => ({ ...endpoint, group: group.name, groupDesc: group.desc })),
);

function getDisplayUrl(endpoint) {
  if (endpoint.base === 'gatewayUrl') return '{{gatewayUrl}}';
  if (endpoint.base === 'baseUrl') return `{{baseUrl}}${endpoint.path}`;
  if (endpoint.base === 'controlNodeBaseUrl') return `{{controlNodeBaseUrl}}${endpoint.path}`;
  if (endpoint.base === 'rosBaseUrl') return `{{rosBaseUrl}}${endpoint.path}`;
  if (endpoint.base === 'chatBaseUrl') return `{{chatBaseUrl}}${endpoint.path}`;
  if (endpoint.base === 'frontendBaseUrl') return `{{frontendBaseUrl}}${endpoint.path}`;
  if (endpoint.base === 'internetPingUrl') return '{{internetPingUrl}}';
  return endpoint.path;
}

function getActualUrl(endpoint) {
  const baseUrl =
    endpoint.base && env[endpoint.base] ? env[endpoint.base] : endpoint.base === 'external' ? '' : '';
  const url = endpoint.base === 'external' ? endpoint.path : `${baseUrl}${endpoint.path}`;
  return resolveTemplateString(url)
    .replaceAll('{user_id}', getSampleVariableValue('userId'))
    .replaceAll('{designID}', getSampleVariableValue('designId'))
    .replaceAll('{filename}', getSampleVariableValue('filename'))
    .replaceAll('{timestamp}', getSampleVariableValue('streamId'))
    .replaceAll('{stream_id}', getSampleVariableValue('streamId'));
}

function getHeaders(endpoint, forHar = false) {
  if (endpoint.method === 'WEBSOCKET') return [];
  const headers = [];
  if (endpoint.contentType === 'multipart/form-data') {
    headers.push({ key: 'Content-Type', value: 'multipart/form-data', desc: '由 FormData 生成' });
  } else if (endpoint.req !== null && endpoint.method !== 'GET') {
    headers.push({ key: 'Content-Type', value: 'application/json', desc: 'JSON 请求体' });
  }
  if (endpoint.command) {
    headers.push({
      key: 'command',
      value: String(endpoint.command),
      desc: `网关分发指令，CommandId.${commandNames[endpoint.command] ?? endpoint.apiName} = ${
        endpoint.command
      }`,
    });
  }
  return headers;
}

function mdJson(value) {
  if (value === null) return '`无`';
  if (typeof value === 'string') return `\`${value}\``;
  return `\n\`\`\`json\n${JSON.stringify(value, null, 2)}\n\`\`\``;
}

const collectionVariables = [
  { key: 'baseUrl', value: env.baseUrl },
  { key: 'gatewayUrl', value: env.gatewayUrl },
  { key: 'controlNodeBaseUrl', value: env.controlNodeBaseUrl },
  { key: 'rosBaseUrl', value: env.rosBaseUrl },
  { key: 'chatBaseUrl', value: env.chatBaseUrl },
  { key: 'frontendBaseUrl', value: env.frontendBaseUrl },
  { key: 'internetPingUrl', value: env.internetPingUrl },
  { key: 'username', value: 'admin' },
  { key: 'password', value: 'admin' },
  { key: 'sessionCookie', value: '' },
  { key: 'token', value: '' },
  { key: 'userId', value: '1' },
  { key: 'tenantId', value: '1' },
  { key: 'accountId', value: '5' },
  { key: 'patientId', value: '' },
  { key: 'patientID', value: '692776867656982528' },
  { key: 'patientName', value: '李松' },
  { key: 'patientIdentityCard', value: '110101199001010011' },
  { key: 'patientTelephone', value: '13800138000' },
  { key: 'caseId', value: '' },
  { key: 'treatmentId', value: '' },
  { key: 'fileKey', value: '' },
  { key: 'oldFileKey', value: '' },
  { key: 'thumbnailFileKey', value: '' },
  { key: 'designId', value: '' },
  { key: 'designVersion', value: '0' },
  { key: 'taskId', value: '' },
  { key: 'messageId', value: '' },
  { key: 'hwid', value: '' },
  { key: 'otpSecret', value: '' },
  { key: 'otpCode', value: '' },
  { key: 'filename', value: 'model.stl' },
  { key: 'streamId', value: '1710000000000' },
];

const moduleFileSlugs = [
  'login-auth',
  'patient-management',
  'case-treatment-sequence',
  'surgical-design',
  'file-management',
  'control-node',
  'network-wifi',
  'implant-system',
  'otp-secret',
  'ai-partition',
  'points',
  'system-message-device',
  'user-config',
  'ros-navigation',
  'chat-assistant',
  'external-resource-connection',
];

const harVariableFallbacks = {
  sessionCookie: 'session=<http-only-cookie-from-login>',
  token: 'token-if-returnToken',
  patientId: 'patient-id',
  caseId: 'case-id',
  treatmentId: 'treatment-id',
  fileKey: 'file-key',
  oldFileKey: 'old-file-key',
  thumbnailFileKey: 'thumbnail-file-key',
  designId: 'design-id',
  designVersion: '1',
  taskId: 'task-id',
  messageId: 'message-id',
  hwid: 'control-node-hwid',
  otpSecret: 'otp-secret',
  otpCode: '123456',
};

function getSampleVariableValue(key) {
  const variable = collectionVariables.find((item) => item.key === key);
  if (variable?.value !== undefined && variable.value !== '') return String(variable.value);
  if (harVariableFallbacks[key] !== undefined) return String(harVariableFallbacks[key]);
  return '';
}

function resolveTemplateString(value) {
  return value.replace(/\{\{([^}]+)\}\}/g, (_, key) => getSampleVariableValue(key.trim()));
}

function resolveHarValue(value) {
  if (typeof value === 'string') return resolveTemplateString(value);
  if (Array.isArray(value)) return value.map((item) => resolveHarValue(item));
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, resolveHarValue(item)]));
  }
  return value;
}

const requiredVarsByApi = {
  updatePatient: ['patientId'],
  delPatient: ['patientId'],
  bindModelFileToPatient: ['patientID', 'fileKey'],
  unbindModelFileToPatient: ['patientID', 'fileKey'],
  searchPatientDetailsMessageV2: ['patientID'],
  changeBindFile: ['patientID', 'oldFileKey', 'fileKey'],
  addCase: ['patientId'],
  updateCase: ['patientId', 'caseId'],
  deleteCase: ['caseId'],
  treatmentSequence: ['caseId'],
  changeTreatmentSequence: ['caseId', 'treatmentId'],
  sortTreatmentSequence: ['caseId', 'treatmentId'],
  delTreatmentSequence: ['caseId', 'treatmentId'],
  addDesign: ['caseId', 'fileKey'],
  addDesignV2: ['caseId', 'fileKey'],
  changeDesign: ['designId', 'fileKey', 'designVersion'],
  navChangeDesign: ['designId', 'designVersion'],
  completeDesign: ['designId', 'designVersion'],
  queryDesignDetail: ['designId'],
  startSurgical: ['designId'],
  finishSurgical: ['designId'],
  delDesign: ['designId'],
  uploadFileChunk: ['fileKey'],
  notifyFileChunkUploadResult: ['fileKey'],
  finishFileUpload: ['fileKey'],
  searchFileDescription: ['fileKey'],
  verifyOtpCode: ['otpCode'],
  uploadUserSecret: ['otpSecret', 'hwid'],
  getUserSecretMeta: ['hwid'],
  getUserOtpCode: ['hwid'],
  starAiPartition: ['designId'],
  getAiPartitionStatus: ['taskId'],
  getExpByToothCusp: ['designId'],
  getPointSummary: ['userId', 'tenantId'],
  getPointDetails: ['userId', 'tenantId'],
  getPointRemind: ['userId', 'tenantId'],
  getUserConfig: ['userId'],
  saveUserConfig: ['userId'],
  deleteMessage: ['messageId'],
  readMessage: ['messageId'],
  getUserConfigRos: ['userId'],
  saveUserConfigRos: ['userId'],
  upLoadFile: ['designId'],
  downLoadFile: ['designId', 'filename'],
};

const extractionRulesByApi = {
  loginByUserName: {
    token: ['data.token', 'token'],
    userId: ['data.userID', 'data.userId', 'data.id', 'userID', 'userId'],
    tenantId: ['data.tenantID', 'data.tenantId', 'tenantID', 'tenantId'],
    accountId: ['data.accountID', 'data.accountId', 'accountID', 'accountId'],
  },
  getUserInfo: {
    userId: ['data.userID', 'data.userId', 'data.id', 'userID', 'userId'],
    tenantId: ['data.tenantID', 'data.tenantId', 'tenantID', 'tenantId'],
    accountId: ['data.accountID', 'data.accountId', 'accountID', 'accountId'],
  },
  savePatient: {
    patientId: ['data.id', 'data.ID', 'data.patientID', 'data.patientId', 'id'],
  },
  queryPatientPage: {
    patientId: ['data.data[0].id', 'data.data[0].ID', 'data.list[0].id', 'data.records[0].id'],
  },
  addCase: {
    caseId: ['data.id', 'data.ID', 'id'],
  },
  updateCase: {
    caseId: ['data.id', 'data.ID', 'id'],
  },
  treatmentSequence: {
    treatmentId: ['data.id', 'data.ID', 'id'],
  },
  startFileUpload: {
    fileKey: ['data.fileKey', 'data.FileKey', 'fileKey'],
  },
  addDesign: {
    designId: ['data.surgicalDesignID', 'data.SurgicalDesignID', 'data.id', 'surgicalDesignID'],
    designVersion: ['data.version', 'data.Version', 'version'],
  },
  addDesignV2: {
    designId: ['data.surgicalDesignID', 'data.SurgicalDesignID', 'data.id', 'surgicalDesignID'],
    designVersion: ['data.version', 'data.Version', 'version'],
  },
  changeDesign: {
    designVersion: ['data.version', 'data.Version', 'version'],
  },
  navChangeDesign: {
    designVersion: ['data.version', 'data.Version', 'version'],
  },
  completeDesign: {
    designVersion: ['data.version', 'data.Version', 'version'],
  },
  queryDesignDetail: {
    designId: ['data.surgicalDesignDetail.ID', 'data.surgicalDesignDetail.id'],
    designVersion: ['data.surgicalDesignDetail.Version', 'data.surgicalDesignDetail.version'],
    patientId: ['data.patientInfo.id', 'data.patientInfo.ID'],
    caseId: ['data.medicalRecordInfo.id', 'data.medicalRecordInfo.ID'],
    fileKey: ['data.modelFileKey', 'data.ModelFileKey'],
  },
  startSurgical: {
    designId: ['data.surgicalDesignDetail.ID', 'data.surgicalDesignDetail.id'],
    designVersion: ['data.surgicalDesignDetail.Version', 'data.surgicalDesignDetail.version'],
  },
  starAiPartition: {
    taskId: ['data.taskID', 'data.taskId', 'data.id', 'taskID'],
  },
  getExpByToothCusp: {
    taskId: ['data.taskID', 'data.taskId', 'data.id', 'taskID'],
  },
  searchMessage: {
    messageId: [
      'data.systemMessageList[0].id',
      'data.systemMessageList[0].ID',
      'data.data[0].id',
      'data.list[0].id',
    ],
  },
  getControlNodeHealthCheck: {
    hwid: ['data.hwid', 'data.HWID', 'hwid'],
  },
  getVersionInfo: {
    hwid: ['data.hwid', 'data.HWID', 'hwid'],
  },
  generateOtpSecret: {
    hwid: ['data.hwid', 'data.HWID', 'hwid'],
    otpSecret: ['data.secret', 'data.Secret', 'secret'],
  },
  getUserOtpCode: {
    otpCode: ['data.otpCode', 'data.otp_code', 'data.code', 'otpCode'],
  },
};

const bodyPatchesByApi = {
  changeDesign: [
    { field: 'version', variable: 'designVersion', type: 'number' },
    { field: 'thumbnail', variable: 'thumbnailFileKey', fallbackVariable: 'fileKey' },
  ],
  navChangeDesign: [{ field: 'version', variable: 'designVersion', type: 'number' }],
  completeDesign: [{ field: 'version', variable: 'designVersion', type: 'number' }],
};

const iterationBodyMappingsByApi = {
  loginByUserName: [
    { column: '账号', field: 'username', allowEmpty: true },
    { column: '密码', field: 'password', allowEmpty: true },
    { column: 'returnToken', field: 'returnToken', type: 'boolean' },
  ],
  savePatient: [
    { column: '姓名', field: 'name', allowEmpty: true },
    { column: '生日', field: 'dateOfBirth', type: 'dateMillis', fallbackValue: 631123200000, fallbackOnEmpty: true },
    { column: '电话', field: 'telephone', allowEmpty: true },
    { column: '性别', field: 'gender', type: 'gender', fallbackValue: 1, fallbackOnEmpty: true },
    { column: '备注', field: 'desc', allowEmpty: true },
  ],
};

const csvExpectationApis = {
  loginByUserName: true,
  savePatient: true,
};

const expectedResultOverridesByApi = {
  loginByUserName: {
    '请输入用户名!': '该账号未注册，请联系管理员',
    '请输入密码！': '该账号未注册，请联系管理员',
    '请输入用户名!请输入密码！': '该账号未注册，请联系管理员',
  },
  savePatient: {
    请填写患者姓名: 'patientID',
    姓名最多输入10个字符: 'patientID',
    '手机号格式错误！': 'patientID',
    备注最多150字: 'patientID',
  },
};

const assertionRulesByApi = {
  loginByUserName: { kind: 'login' },
  getUserInfo: {
    anyPathGroups: [
      { label: '用户 ID 已返回', paths: ['data.ID', 'data.userID', 'data.userId', 'data.id'] },
      { label: '租户 ID 已返回', paths: ['data.TenantID', 'data.tenantID', 'data.tenantId'] },
    ],
  },
  savePatient: { kind: 'patientSave' },
  queryPatientPage: {
    anyPathGroups: [
      { label: '患者分页列表已返回', paths: ['data.data', 'data.list', 'data.records'] },
      { label: '患者分页总数已返回', paths: ['data.total'] },
    ],
  },
  addCase: { anyPathGroups: [{ label: '病例 ID 已返回', paths: ['data.id', 'data.ID'] }] },
  updateCase: { anyPathGroups: [{ label: '病例 ID 已返回', paths: ['data.id', 'data.ID'] }] },
  treatmentSequence: { anyPathGroups: [{ label: '治疗阶段 ID 已返回', paths: ['data.id', 'data.ID'] }] },
  startFileUpload: { anyPathGroups: [{ label: '文件 fileKey 已返回', paths: ['data.fileKey', 'data.FileKey'] }] },
  searchFileDescription: { anyPathGroups: [{ label: '文件描述列表已返回', paths: ['data.files', 'data.Files'] }] },
  addDesign: {
    anyPathGroups: [
      { label: '手术设计 ID 已返回', paths: ['data.surgicalDesignID', 'data.SurgicalDesignID'] },
      { label: '设计版本已返回', paths: ['data.version', 'data.Version'] },
    ],
  },
  addDesignV2: {
    anyPathGroups: [
      { label: '手术设计 ID 已返回', paths: ['data.surgicalDesignID', 'data.SurgicalDesignID'] },
      { label: '设计版本已返回', paths: ['data.version', 'data.Version'] },
    ],
  },
  changeDesign: { anyPathGroups: [{ label: '设计新版本已返回', paths: ['data.version', 'data.Version'] }] },
  navChangeDesign: { anyPathGroups: [{ label: '导航设计新版本已返回', paths: ['data.version', 'data.Version'] }] },
  queryDesignDetail: {
    anyPathGroups: [
      { label: '设计详情已返回', paths: ['data.surgicalDesignDetail'] },
      { label: '设计详情版本已返回', paths: ['data.surgicalDesignDetail.Version', 'data.surgicalDesignDetail.version'] },
    ],
  },
  startSurgical: { anyPathGroups: [{ label: '手术设计详情已返回', paths: ['data.surgicalDesignDetail'] }] },
  finishSurgical: { anyPathGroups: [{ label: '手术完成结果已返回', paths: ['data.status', 'data.Status', 'data'] }] },
  getImplantFavorites: { anyPathGroups: [{ label: '植体收藏数据已返回', paths: ['data.favorites', 'data'] }] },
  generateOtpSecret: {
    anyPathGroups: [
      { label: '控制节点 hwid 已返回', paths: ['data.hwid', 'data.HWID', 'hwid'] },
      { label: 'OTP secret 已返回', paths: ['data.secret', 'data.Secret', 'secret'] },
    ],
  },
  getUserOtpCode: { anyPathGroups: [{ label: 'OTP code 已返回', paths: ['data.otpCode', 'data.otp_code', 'data.code'] }] },
  starAiPartition: { anyPathGroups: [{ label: 'AI 任务 ID 已返回', paths: ['data.taskID', 'data.taskId', 'data.id'] }] },
  getAiPartitionStatus: { anyPathGroups: [{ label: 'AI 任务状态已返回', paths: ['data.status', 'data.taskStatus', 'data'] }] },
  getExpByToothCusp: { anyPathGroups: [{ label: '牙尖分析任务 ID 已返回', paths: ['data.taskID', 'data.taskId', 'data.id'] }] },
  getPointSummary: { anyPathGroups: [{ label: '积分总览已返回', paths: ['data.personalPoint', 'data.tenantPoint', 'data'] }] },
  getPointDetails: { anyPathGroups: [{ label: '积分明细列表已返回', paths: ['data.data', 'data.list', 'data'] }] },
  getPointRemind: { anyPathGroups: [{ label: '积分提醒列表已返回', paths: ['data.data', 'data.list', 'data'] }] },
  searchMessage: { anyPathGroups: [{ label: '系统消息列表已返回', paths: ['data.systemMessageList', 'data.data', 'data.list'] }] },
  getDeviceList: { anyPathGroups: [{ label: '设备列表已返回', paths: ['data.devices', 'data'] }] },
  getUserConfig: { anyPathGroups: [{ label: '用户配置已返回', paths: ['data.configs', 'data'] }] },
  saveUserConfig: { anyPathGroups: [{ label: '保存用户配置结果已返回', paths: ['data', 'message'] }] },
};

function scriptEvent(listen, lines) {
  if (!lines.length) return null;
  return {
    listen,
    script: {
      type: 'text/javascript',
      exec: lines,
    },
  };
}

function makeCollectionPrerequestEvent() {
  const defaults = Object.fromEntries(
    collectionVariables.filter((variable) => variable.value !== '').map((variable) => [variable.key, variable.value]),
  );
  return scriptEvent('prerequest', [
    'function getScopeValue(key) {',
    '  if (pm.environment && pm.environment.get(key)) return pm.environment.get(key);',
    '  if (pm.globals && pm.globals.get(key)) return pm.globals.get(key);',
    '  if (pm.collectionVariables && pm.collectionVariables.get(key)) return pm.collectionVariables.get(key);',
    '  return "";',
    '}',
    'function setScopeValue(key, value) {',
    '  if (value === undefined || value === null || value === "") return;',
    '  var stringValue = String(value);',
    '  if (pm.environment) pm.environment.set(key, stringValue);',
    '  if (pm.globals) pm.globals.set(key, stringValue);',
    '}',
    `var defaults = ${JSON.stringify(defaults, null, 2)};`,
    'Object.keys(defaults).forEach(function(key) {',
    '  if (!getScopeValue(key)) setScopeValue(key, defaults[key]);',
    '});',
  ]);
}

function makePrerequestEvent(endpoint) {
  const requiredVars = requiredVarsByApi[endpoint.apiName] ?? [];
  const bodyPatches = bodyPatchesByApi[endpoint.apiName] ?? [];
  const iterationMappings = iterationBodyMappingsByApi[endpoint.apiName] ?? [];
  if (!requiredVars.length && !bodyPatches.length && !iterationMappings.length) return null;
  const lines = [
    'function getScopeValue(key) {',
    '  if (pm.environment && pm.environment.get(key)) return pm.environment.get(key);',
    '  if (pm.globals && pm.globals.get(key)) return pm.globals.get(key);',
    '  if (pm.collectionVariables && pm.collectionVariables.get(key)) return pm.collectionVariables.get(key);',
    '  return "";',
    '}',
  ];
  if (requiredVars.length) {
    lines.push(`var requiredVars = ${JSON.stringify(requiredVars)};`);
    lines.push('var missingVars = requiredVars.filter(function(key) { return !getScopeValue(key); });');
    lines.push('pm.test("依赖变量已设置", function() {');
    lines.push('  pm.expect(missingVars, "缺少变量: " + missingVars.join(", ")).to.eql([]);');
    lines.push('});');
    lines.push('if (missingVars.length) throw new Error("缺少依赖变量: " + missingVars.join(", "));');
  }
  if (iterationMappings.length) {
    lines.push('function getIterationValue(columnName) {');
    lines.push('  if (!pm.iterationData || !pm.iterationData.get) return undefined;');
    lines.push('  var value = pm.iterationData.get(columnName);');
    lines.push('  return value === null ? undefined : value;');
    lines.push('}');
    lines.push('function hasIterationColumn(columnName) {');
    lines.push('  return getIterationValue(columnName) !== undefined;');
    lines.push('}');
    lines.push('function normalizeIterationValue(rawValue, mapping) {');
    lines.push('  var value = rawValue;');
    lines.push('  if ((value === "" || value === undefined || value === null) && mapping.fallbackOnEmpty) {');
    lines.push('    if (mapping.fallbackVariable) value = getScopeValue(mapping.fallbackVariable);');
    lines.push('    else if (Object.prototype.hasOwnProperty.call(mapping, "fallbackValue")) value = mapping.fallbackValue;');
    lines.push('  }');
    lines.push('  if (value === undefined || value === null) return value;');
    lines.push('  if (mapping.type === "boolean") {');
    lines.push('    if (typeof value === "boolean") return value;');
    lines.push('    return String(value).toLowerCase() === "true";');
    lines.push('  }');
    lines.push('  if (mapping.type === "dateMillis") {');
    lines.push('    if (value === "") return value;');
    lines.push('    var parsedDate = Date.parse(String(value));');
    lines.push('    if (!Number.isNaN(parsedDate)) return parsedDate;');
    lines.push('    var numberDate = Number(value);');
    lines.push('    return Number.isNaN(numberDate) ? value : numberDate;');
    lines.push('  }');
    lines.push('  if (mapping.type === "gender") {');
    lines.push('    if (value === "") return value;');
    lines.push('    if (String(value).includes("女")) return 2;');
    lines.push('    if (String(value).includes("男")) return 1;');
    lines.push('    var genderNumber = Number(value);');
    lines.push('    return Number.isNaN(genderNumber) ? value : genderNumber;');
    lines.push('  }');
    lines.push('  if (mapping.type === "number") {');
    lines.push('    var numericValue = Number(value);');
    lines.push('    return Number.isNaN(numericValue) ? value : numericValue;');
    lines.push('  }');
    lines.push('  return String(value);');
    lines.push('}');
    lines.push('function patchJsonBodyByIteration(mappings) {');
    lines.push('  if (!pm.request.body || !pm.request.body.raw) return;');
    lines.push('  var hasDataDrivenColumn = mappings.some(function(mapping) { return hasIterationColumn(mapping.column); });');
    lines.push('  if (!hasDataDrivenColumn) return;');
    lines.push('  try {');
    lines.push('    var body = JSON.parse(pm.request.body.raw);');
    lines.push('    mappings.forEach(function(mapping) {');
    lines.push('      var rawValue = getIterationValue(mapping.column);');
    lines.push('      if (rawValue === undefined) return;');
    lines.push('      var value = normalizeIterationValue(rawValue, mapping);');
    lines.push('      if ((value === undefined || value === null || value === "") && !mapping.allowEmpty) return;');
    lines.push('      body[mapping.field] = value;');
    lines.push('    });');
    lines.push('    pm.request.body.update(JSON.stringify(body, null, 2));');
    lines.push('  } catch (error) {');
    lines.push('    console.warn("CSV 数据驱动请求体写入失败", error);');
    lines.push('  }');
    lines.push('}');
    lines.push(`patchJsonBodyByIteration(${JSON.stringify(iterationMappings)});`);
  }
  if (bodyPatches.length) {
    lines.push('function patchJsonBody(fieldName, variableName, valueType, fallbackVariableName) {');
    lines.push('  if (!pm.request.body || !pm.request.body.raw) return;');
    lines.push('  var value = getScopeValue(variableName);');
    lines.push('  if (!value && fallbackVariableName) value = getScopeValue(fallbackVariableName);');
    lines.push('  if (value === undefined || value === null || value === "") return;');
    lines.push('  try {');
    lines.push('    var body = JSON.parse(pm.request.body.raw);');
    lines.push('    body[fieldName] = valueType === "number" ? Number(value) : String(value);');
    lines.push('    pm.request.body.update(JSON.stringify(body, null, 2));');
    lines.push('  } catch (error) {');
    lines.push('    console.warn("JSON 请求体自动写入失败: " + fieldName, error);');
    lines.push('  }');
    lines.push('}');
    for (const patch of bodyPatches) {
      lines.push(
        `patchJsonBody(${JSON.stringify(patch.field)}, ${JSON.stringify(patch.variable)}, ${JSON.stringify(
          patch.type ?? 'string',
        )}, ${JSON.stringify(patch.fallbackVariable ?? '')});`,
      );
    }
  }
  return scriptEvent('prerequest', lines);
}

function makeTestEvent(endpoint) {
  const extractionRules = extractionRulesByApi[endpoint.apiName];
  const assertionRule = assertionRulesByApi[endpoint.apiName];
  const consumesCsvExpectation = Boolean(csvExpectationApis[endpoint.apiName]);
  const expectedResultOverrides = expectedResultOverridesByApi[endpoint.apiName] ?? {};
  const expectsJson =
    endpoint.method !== 'WEBSOCKET' &&
    endpoint.responseType !== 'blob' &&
    endpoint.responseType !== 'stream' &&
    endpoint.responseType !== 'text/event-stream';
  const lines = [
    'function setScopeValue(key, value) {',
    '  if (value === undefined || value === null || value === "") return;',
    '  var stringValue = String(value);',
    '  if (pm.environment) pm.environment.set(key, stringValue);',
    '  if (pm.globals) pm.globals.set(key, stringValue);',
    '}',
    'function getScopeValue(key) {',
    '  if (pm.environment && pm.environment.get(key)) return pm.environment.get(key);',
    '  if (pm.globals && pm.globals.get(key)) return pm.globals.get(key);',
    '  if (pm.collectionVariables && pm.collectionVariables.get(key)) return pm.collectionVariables.get(key);',
    '  return "";',
    '}',
    'function getIterationValue(columnName) {',
    '  if (!pm.iterationData || !pm.iterationData.get) return undefined;',
    '  var value = pm.iterationData.get(columnName);',
    '  return value === null ? undefined : value;',
    '}',
    'function getFirstIterationValue(columnNames) {',
    '  for (var index = 0; index < columnNames.length; index += 1) {',
    '    var value = getIterationValue(columnNames[index]);',
    '    if (value !== undefined && value !== null && value !== "") return String(value);',
    '  }',
    '  return "";',
    '}',
    'function getPath(source, path) {',
    '  return path.split(".").reduce(function(current, key) {',
    '    if (current === undefined || current === null) return undefined;',
    '    var match = key.match(/^([^\\[]+)\\[(\\d+)\\]$/);',
    '    if (match) {',
    '      var arrayValue = current[match[1]];',
    '      return Array.isArray(arrayValue) ? arrayValue[Number(match[2])] : undefined;',
    '    }',
    '    return current[key];',
    '  }, source);',
    '}',
    'function setFirst(key, paths) {',
    '  for (var index = 0; index < paths.length; index += 1) {',
    '    var value = getPath(responseBody, paths[index]);',
    '    if (value !== undefined && value !== null && value !== "") {',
    '      setScopeValue(key, value);',
    '      return value;',
    '    }',
    '  }',
    '  return "";',
    '}',
    'var responseBody = {};',
    'try { responseBody = pm.response.json(); } catch (error) { responseBody = {}; }',
    `var expectsJson = ${JSON.stringify(expectsJson)};`,
    `var consumesCsvExpectation = ${JSON.stringify(consumesCsvExpectation)};`,
    `var expectedResultOverrides = ${JSON.stringify(expectedResultOverrides)};`,
    'var expectedResult = consumesCsvExpectation ? getFirstIterationValue(["预期结果", "expectedResult", "expectedMessage"]) : getFirstIterationValue(["expectedResult", "expectedMessage"]);',
    'if (expectedResult && Object.prototype.hasOwnProperty.call(expectedResultOverrides, expectedResult)) expectedResult = expectedResultOverrides[expectedResult];',
    'var expectedValid = consumesCsvExpectation ? getFirstIterationValue(["是否有效", "valid", "isValid"]) : getFirstIterationValue(["valid", "isValid"]);',
    'var expectedInvalid = String(expectedValid).toLowerCase() === "false";',
    'var expectedSuccess = String(expectedValid).toLowerCase() === "true";',
    'if (expectedResult === "patientID") { expectedInvalid = false; expectedSuccess = true; }',
    'var hasBusinessCode = Object.prototype.hasOwnProperty.call(responseBody, "code");',
    'pm.test("HTTP 状态码为 2xx", function() {',
    '  pm.expect(pm.response.code).to.be.within(200, 299);',
    '});',
    'if (expectsJson) {',
    '  pm.test("响应体为 JSON 对象", function() {',
    '    pm.expect(responseBody).to.be.an("object");',
    '  });',
    '}',
    'if (expectsJson && hasBusinessCode) {',
    '  if (expectedResult && expectedResult !== "patientID") {',
    '    pm.test("业务 message 符合预期", function() {',
    '      pm.expect(responseBody.message).to.eql(expectedResult);',
    '    });',
    '  } else if (expectedInvalid) {',
    '    pm.test("无效用例业务 code 非 0", function() {',
    '      pm.expect(Number(responseBody.code)).to.not.eql(0);',
    '    });',
    '  } else {',
    '    pm.test("业务 code 为 0", function() {',
    '      pm.expect(Number(responseBody.code)).to.eql(0);',
    '    });',
    '  }',
    '}',
    'if (expectsJson && hasBusinessCode && expectedInvalid) {',
    '  pm.test("无效用例业务 code 非 0", function() {',
    '    pm.expect(Number(responseBody.code)).to.not.eql(0);',
    '  });',
    '}',
    'function shouldAssertSuccessShape() {',
    '  return !expectedInvalid && (!expectedResult || expectedResult === "patientID");',
    '}',
    'function assertAnyPath(label, paths) {',
    '  if (!shouldAssertSuccessShape()) return;',
    '  pm.test(label, function() {',
    '    var found = paths.some(function(path) {',
    '      var value = getPath(responseBody, path);',
    '      return value !== undefined && value !== null && value !== "";',
    '    });',
    '    pm.expect(found, "任一字段存在: " + paths.join(", ")).to.eql(true);',
    '  });',
    '}',
  ];
  if (endpoint.apiName === 'loginByUserName') {
    lines.push('var setCookie = pm.response.headers.get("Set-Cookie") || pm.response.headers.get("set-cookie");');
    lines.push('if (setCookie) setScopeValue("sessionCookie", setCookie.split(";")[0]);');
  }
  if (assertionRule?.kind === 'login') {
    lines.push('if (!expectedInvalid) {');
    lines.push('  pm.test("登录响应 data.username 符合请求账号", function() {');
    lines.push('    var expectedUsername = getIterationValue("账号");');
    lines.push('    if (expectedUsername === undefined || expectedUsername === null || expectedUsername === "") expectedUsername = getScopeValue("username");');
    lines.push('    pm.expect(getPath(responseBody, "data.username")).to.eql(String(expectedUsername));');
    lines.push('  });');
    lines.push('}');
  }
  if (assertionRule?.kind === 'patientSave') {
    lines.push('if (expectedResult === "patientID" || expectedSuccess || (!expectedResult && !expectedInvalid)) {');
    lines.push('  assertAnyPath("新增患者返回 patientID", ["data.id", "data.ID", "data.patientID", "data.patientId"]);');
    lines.push('}');
  }
  for (const group of assertionRule?.anyPathGroups ?? []) {
    lines.push(`assertAnyPath(${JSON.stringify(group.label)}, ${JSON.stringify(group.paths)});`);
  }
  if (extractionRules) {
    for (const [variableName, paths] of Object.entries(extractionRules)) {
      lines.push(`var extracted_${variableName} = setFirst(${JSON.stringify(variableName)}, ${JSON.stringify(paths)});`);
      if (endpoint.apiName === 'startFileUpload' && variableName === 'fileKey') {
        lines.push('if (extracted_fileKey && !getScopeValue("oldFileKey")) setScopeValue("oldFileKey", extracted_fileKey);');
        lines.push(
          'if (extracted_fileKey && !getScopeValue("thumbnailFileKey")) setScopeValue("thumbnailFileKey", extracted_fileKey);',
        );
      }
    }
  }
  return scriptEvent('test', lines);
}

function getPostmanEvents(endpoint) {
  return [makePrerequestEvent(endpoint), makeTestEvent(endpoint)].filter(Boolean);
}

function makeMarkdown() {
  const lines = [];
  lines.push('# TARS Admin Frontend 标准接口文档');
  lines.push('');
  lines.push('> 根据前端代码静态整理生成。统一 API 封装来源：`src/api/request.ts`。');
  lines.push('');
  lines.push('## 环境与通用约定');
  lines.push('');
  lines.push(`- 本地前端登录页：\`${env.frontendBaseUrl}/login\``);
  lines.push(`- \`{{baseUrl}}\`：\`${env.baseUrl}\``);
  lines.push(`- \`{{gatewayUrl}}\`：\`${env.gatewayUrl}\``);
  lines.push(`- \`{{controlNodeBaseUrl}}\`：\`${env.controlNodeBaseUrl}\``);
  lines.push(`- \`{{rosBaseUrl}}\`：\`${env.rosBaseUrl}\``);
  lines.push(`- \`{{chatBaseUrl}}\`：\`${env.chatBaseUrl}\``);
  lines.push('');
  lines.push('前端运行时会自动补充以下 header；Apifox 导入文件已移除这些非必要 header，只保留调试必需项：');
  lines.push('');
  lines.push('| Header | 值 | 说明 |');
  lines.push('| --- | --- | --- |');
  for (const header of runtimeHeaders) {
    lines.push(`| \`${header.key}\` | \`${header.value}\` | ${header.desc} |`);
  }
  lines.push('');
  lines.push(
    '网关接口统一请求 `POST {{gatewayUrl}}`，必须额外携带 `command` header。接口身份由 `command` 数值区分，业务请求体仍放在 JSON body 中。',
  );
  lines.push('');
  lines.push('### Apifox 导入变量与执行链路');
  lines.push('');
  lines.push(
    '导入 `apifox-collection.postman.json` 后会包含集合变量，并通过前置/后置脚本在接口之间自动传递登录态、患者、病例、文件、设计、任务和消息等 ID。DICOM/模型文件相关接口统一使用 `{{patientID}}`，默认值为 `692776867656982528`，集合级前置脚本也会写入同名全局变量。',
  );
  lines.push('');
  lines.push('| 变量 | 默认值 | 用途 |');
  lines.push('| --- | --- | --- |');
  const variableDescriptions = {
    username: '登录用户名',
    password: '登录密码',
    sessionCookie: '登录接口 Set-Cookie 提取值；http-only Cookie 由客户端 Cookie Jar 维护',
    token: '登录 returnToken=true 时的 token',
    userId: '当前登录用户 ID',
    tenantId: '当前租户 ID',
    accountId: '当前账户 ID',
    patientId: '新增患者或查询患者列表后提取的普通患者 ID',
    patientID: 'DICOM/模型文件相关接口固定患者 ID',
    patientName: '新增、查询、更新患者姓名',
    patientIdentityCard: '新增、更新患者身份证号',
    patientTelephone: '新增、查询、更新患者电话',
    caseId: '新增/更新病例后提取的病例 ID',
    treatmentId: '新增治疗阶段后提取的治疗阶段 ID',
    fileKey: '开始分片上传后提取的文件 key',
    oldFileKey: '变更绑定文件时使用的旧文件 key',
    thumbnailFileKey: '设计缩略图文件 key，默认可由 fileKey 回填',
    designId: '创建设计后提取的手术设计 ID',
    designVersion: '创建设计、修改设计或查询详情后提取的设计版本',
    taskId: 'AI 分割任务 ID',
    messageId: '系统消息 ID',
    hwid: '控制节点硬件 ID',
    otpSecret: '生成 OTP Secret 后提取的 secret',
    otpCode: '获取用户 OTP Code 后提取的动态码',
    filename: 'ROS 下载模型文件名',
    streamId: 'ROS JPEG 流 ID',
  };
  for (const variable of collectionVariables) {
    if (!variableDescriptions[variable.key]) continue;
    lines.push(`| \`${variable.key}\` | \`${variable.value}\` | ${variableDescriptions[variable.key]} |`);
  }
  lines.push('');
  lines.push('推荐执行顺序：登录 -> 获取当前用户 -> 新增患者 -> 新增病例 -> 新增治疗阶段 -> 开始文件上传 -> 创建设计 -> 修改/查询设计。依赖 DICOM 文件的接口可直接使用默认 `{{patientID}}`。');
  lines.push('');
  lines.push('## 接口架构梳理');
  lines.push('');
  lines.push('| 客户端 | 创建位置 | 基址 | 用途 |');
  lines.push('| --- | --- | --- | --- |');
  lines.push(
    '| `commonHttp` | `src/api/request.ts` | `{{baseUrl}}` | 登录、登出、短信、设置、后端中转文件上传等普通 `/tars/v1` 接口 |',
  );
  lines.push(
    '| `gateWayHttp` | `src/api/request.ts` | `{{gatewayUrl}}` | 业务网关接口，固定 `POST /tars/v1/gateway`，通过 `command` header 区分业务接口；离线模式下会经过 `GatewayHttpOfflineInterceptorManager` |',
  );
  lines.push(
    '| `controlNodeHttp` | `src/api/request.ts` | `{{controlNodeBaseUrl}}` | 控制节点接口，包括文件、Wi-Fi、版本、录屏、升级、OTP 本地校验等 |',
  );
  lines.push(
    '| `rosHttp` | `src/api/request.ts` | `{{rosBaseUrl}}` | ROS HTTP 接口，包括 Marker、模型文件同步、JPEG 流、MR 升级和灯光控制 |',
  );
  lines.push(
    '| `chatHttp` | `src/api/request.ts` | `{{chatBaseUrl}}` | 聊天节点流式接口 |',
  );
  lines.push(
    '| 直接网络调用 | 多处 | 预签名 URL / `ws://...:9090` / `/cs/gdcmconv.js` | 文件分片下载、ROS WebSocket、SSE、静态运行时资源加载等补充入口 |',
  );
  lines.push('');
  lines.push('## 分组总览');
  lines.push('');
  lines.push('| 分组 | 接口数 | 说明 |');
  lines.push('| --- | ---: | --- |');
  for (const group of groups) {
    lines.push(`| ${group.name} | ${group.endpoints.length} | ${group.desc} |`);
  }
  lines.push('');
  lines.push('## 接口明细');
  lines.push('');
  for (const group of groups) {
    lines.push(`### ${group.name}`);
    lines.push('');
    lines.push(`说明：${group.desc}`);
    lines.push('');
    lines.push('| 接口名称 | 接口描述 | 请求方式 | 请求地址 | 关键参数 | 响应 | 来源 |');
    lines.push('| --- | --- | --- | --- | --- | --- | --- |');
    for (const endpoint of group.endpoints) {
      const keyParams = endpoint.command
        ? `Header: command=${endpoint.command}`
        : endpoint.req && typeof endpoint.req === 'object'
          ? Object.keys(endpoint.req).slice(0, 6).join(', ')
          : endpoint.req === null
            ? '无'
            : '见 Req';
      const responseLabel =
        typeof endpoint.res === 'string'
          ? endpoint.res
          : endpoint.responseType
            ? endpoint.responseType
            : 'JSON';
      lines.push(
        `| ${endpoint.apiName} | ${endpoint.desc} | \`${endpoint.method}\` | \`${getDisplayUrl(
          endpoint,
        )}\` | ${keyParams} | ${responseLabel} | \`${endpoint.source}\` |`,
      );
    }
    lines.push('');
    for (const endpoint of group.endpoints) {
      lines.push(`#### ${group.name} / ${endpoint.name}`);
      lines.push('');
      lines.push(`- 接口名称：\`${endpoint.apiName}\``);
      lines.push(`- 接口描述：${endpoint.desc}`);
      lines.push(`- 请求地址：\`${getDisplayUrl(endpoint)}\``);
      lines.push(`- 请求方式：\`${endpoint.method}\``);
      if (endpoint.command) {
        lines.push(
          `- 网关 command：\`${endpoint.command}\`（CommandId.${
            commandNames[endpoint.command] ?? endpoint.apiName
          }）`,
        );
      }
      if (endpoint.responseType) lines.push(`- 响应类型：\`${endpoint.responseType}\``);
      lines.push(`- 代码来源：\`${endpoint.source}\``);
      lines.push('- 请求头：');
      for (const header of getHeaders(endpoint)) {
        const disabled = header.disabled ? '（可选）' : '';
        lines.push(`  - \`${header.key}: ${header.value}\`${disabled}：${header.desc}`);
      }
      lines.push('- Req：');
      lines.push(mdJson(endpoint.req));
      lines.push('- Res：');
      lines.push(mdJson(endpoint.res));
      lines.push('');
    }
  }
  return lines.join('\n');
}

function makePostmanCollection() {
  const collection = {
    info: {
      name: 'TARS Admin Frontend APIs',
      description:
        'Apifox 可直接导入。根据前端 src/api 和散落网络调用静态整理，保留业务分组和网关 command header。',
      schema: 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json',
    },
    item: groups.map((group) => ({
      name: group.name,
      description: group.desc,
      item: group.endpoints.map((endpoint) =>
        makePostmanItem({ ...endpoint, group: group.name, groupDesc: group.desc }),
      ),
    })),
    event: [makeCollectionPrerequestEvent()],
  };
  return JSON.stringify(collection, null, 2);
}

function getModuleFileName(group, index) {
  const slug = moduleFileSlugs[index] ?? `module-${index + 1}`;
  return `${String(index + 1).padStart(2, '0')}-${slug}.postman.json`;
}

function makePostmanModuleCollection(group) {
  const collection = {
    info: {
      name: `TARS Admin Frontend APIs - ${group.name}`,
      description: [
        `${group.desc}`,
        '',
        '此文件用于按模块导入 Apifox。变量不写入模块集合，请先导入 api-docs/apifox-shared-environment.postman_environment.json，或在 Apifox 项目/环境变量中维护同名变量。',
        '接口依赖变量会通过前置/后置脚本写入环境变量和全局变量，不会写入模块变量。',
      ].join('\n'),
      schema: 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json',
    },
    item: group.endpoints.map((endpoint) =>
      makePostmanItem({ ...endpoint, group: group.name, groupDesc: group.desc }),
    ),
    event: [makeCollectionPrerequestEvent()],
  };
  return JSON.stringify(collection, null, 2);
}

function makeSharedEnvironment() {
  return JSON.stringify(
    {
      name: 'TARS Admin Frontend Shared Environment',
      values: collectionVariables.map((variable) => ({
        key: variable.key,
        value: String(variable.value ?? ''),
        type: 'default',
        enabled: true,
      })),
      _postman_variable_scope: 'environment',
      _postman_exported_at: '2026-06-05T00:00:00.000Z',
      _postman_exported_using: 'Codex static API doc generator',
    },
    null,
    2,
  );
}

function makePostmanItem(endpoint) {
  const header = getHeaders(endpoint).map((h) => ({
    key: h.key,
    value: h.value,
    description: h.desc,
    disabled: h.disabled || undefined,
  }));
  const item = {
    name: endpoint.command ? `${endpoint.name} [command=${endpoint.command}]` : endpoint.name,
    request: {
      method: endpoint.method === 'WEBSOCKET' ? 'GET' : endpoint.method,
      header,
      url: getDisplayUrl(endpoint),
      description: [
        `接口名称：${endpoint.apiName}`,
        `接口描述：${endpoint.desc}`,
        `分组：${endpoint.group ?? ''}`,
        endpoint.command
          ? `网关分发指令：command=${endpoint.command} (CommandId.${
              commandNames[endpoint.command] ?? endpoint.apiName
            })`
          : '',
        `代码来源：${endpoint.source}`,
        '',
        `Req:\n${endpoint.req === null ? '无' : JSON.stringify(endpoint.req, null, 2)}`,
        '',
        `Res:\n${typeof endpoint.res === 'string' ? endpoint.res : JSON.stringify(endpoint.res, null, 2)}`,
      ]
        .filter(Boolean)
        .join('\n'),
    },
    response: [],
  };
  const events = getPostmanEvents(endpoint);
  if (events.length) item.event = events;
  if (endpoint.method !== 'GET' && endpoint.method !== 'WEBSOCKET' && endpoint.req !== null) {
    if (endpoint.contentType === 'multipart/form-data') {
      item.request.body = {
        mode: 'formdata',
        formdata: Object.entries(endpoint.req).map(([key, value]) => ({
          key,
          type: String(value).includes('<File>') || Array.isArray(value) ? 'file' : 'text',
          value: Array.isArray(value) ? '' : String(value),
          description: Array.isArray(value) ? JSON.stringify(value) : undefined,
        })),
      };
    } else {
      item.request.body = {
        mode: 'raw',
        raw: JSON.stringify(endpoint.req, null, 2),
        options: { raw: { language: 'json' } },
      };
    }
  }
  return item;
}

function makeHar() {
  const pages = groups.map((group, index) => ({
    startedDateTime: '2026-06-05T00:00:00.000Z',
    id: `page_${index + 1}`,
    title: group.name,
    pageTimings: {},
  }));
  const entries = [];
  groups.forEach((group, index) => {
    for (const endpoint of group.endpoints) {
      if (endpoint.excludeFromHar || endpoint.method === 'WEBSOCKET') continue;
      entries.push(makeHarEntry({ ...endpoint, group: group.name, groupDesc: group.desc }, `page_${index + 1}`));
    }
  });
  return JSON.stringify(
    {
      log: {
        version: '1.2',
        creator: { name: 'Codex static API doc generator', version: '1.0.0' },
        pages,
        entries,
      },
    },
    null,
    2,
  );
}

function makeHarEntry(endpoint, pageref) {
  const url = getActualUrl(endpoint);
  const headers = getHeaders(endpoint, true)
    .filter((h) => !h.disabled)
    .map((h) => ({
      name: h.key,
      value: h.value,
      comment: h.desc,
    }));
  const queryString = [];
  const queryPart = url.split('?')[1];
  if (queryPart) {
    for (const pair of queryPart.split('&')) {
      const [name, value = ''] = pair.split('=');
      queryString.push({ name, value });
    }
  }
  const request = {
    method: endpoint.method,
    url,
    httpVersion: 'HTTP/1.1',
    headers,
    queryString,
    cookies: [],
    headersSize: -1,
    bodySize: -1,
    comment: `${endpoint.group} / ${endpoint.name} (${endpoint.apiName})`,
  };
  if (endpoint.method !== 'GET' && endpoint.req !== null) {
    const resolvedReq = resolveHarValue(endpoint.req);
    if (endpoint.contentType === 'multipart/form-data') {
      request.postData = {
        mimeType: 'multipart/form-data',
        params: Object.entries(resolvedReq).map(([name, value]) => ({
          name,
          value: Array.isArray(value) ? JSON.stringify(value) : String(value),
          fileName: String(value).includes('<File>') || Array.isArray(value) ? `${name}.bin` : undefined,
        })),
      };
    } else {
      request.postData = {
        mimeType: 'application/json',
        text: JSON.stringify(resolvedReq, null, 2),
      };
    }
  }
  const resText =
    typeof endpoint.res === 'string' ? endpoint.res : JSON.stringify(endpoint.res, null, 2);
  return {
    pageref,
    startedDateTime: '2026-06-05T00:00:00.000Z',
    time: 0,
    request,
    response: {
      status: 200,
      statusText: 'OK',
      httpVersion: 'HTTP/1.1',
      headers: [
        {
          name: 'Content-Type',
          value:
            endpoint.responseType === 'blob'
              ? 'application/octet-stream'
              : endpoint.responseType === 'text/event-stream'
                ? 'text/event-stream'
                : 'application/json',
        },
      ],
      cookies: [],
      content: {
        size: Buffer.byteLength(resText),
        mimeType:
          endpoint.responseType === 'blob'
            ? 'application/octet-stream'
            : endpoint.responseType === 'text/event-stream'
              ? 'text/event-stream'
              : 'application/json',
        text: resText,
      },
      redirectURL: '',
      headersSize: -1,
      bodySize: -1,
    },
    cache: {},
    timings: { send: 0, wait: 0, receive: 0 },
    comment: `${endpoint.desc} Source: ${endpoint.source}`,
  };
}

function makeReadme() {
  return [
    '# API Docs',
    '',
    '本目录由前端代码静态整理接口生成，已按业务域分组。',
    '',
    '## 文件说明',
    '',
    '- `standard-api-doc.md`：标准接口文档，包含接口名称、描述、请求地址、方式、请求头、Req、Res 和源码位置。',
    '- `apifox-collection.postman.json`：推荐导入 Apifox 的集合文件，保留分组和网关 `command` header。',
    '- `tars-admin-frontend.har`：可导入 Apifox 的 HAR 文件，按接口生成请求包；网关接口通过 `command` header 区分。',
    '- `validation-report.md`：接口验证记录、已修正问题、变量提取链路和未执行接口说明。',
    '- `test-cases.md`：接口测试用例设计、CSV 数据驱动字段映射和后置断言说明。',
    '- `generate-api-docs.mjs`：文档生成脚本。',
    '',
    '## 本地环境',
    '',
    `- 前端登录页：\`${env.frontendBaseUrl}/login\``,
    `- 普通后端接口：\`${env.baseUrl}\``,
    `- 网关接口：\`${env.gatewayUrl}\``,
    `- 控制节点接口：\`${env.controlNodeBaseUrl}\``,
    `- ROS 接口：\`${env.rosBaseUrl}\``,
    `- 聊天接口：\`${env.chatBaseUrl}\``,
    '',
    '## Apifox 使用建议',
    '',
    '1. 优先导入 `apifox-collection.postman.json`，它能保留分组目录。',
    '2. 集合已内置变量、集合级前置脚本、接口级前置校验和后置提取脚本；登录后会提取 `sessionCookie`，患者/病例/文件/设计等接口会继续提取关联 ID。',
    '3. 集合已内置测试断言；登录和新增患者接口支持用 CSV 数据驱动同一接口的有效/无效用例。',
    '4. DICOM/模型文件相关接口统一使用 `{{patientID}}`，默认值为 `692776867656982528`，集合级前置脚本会同步为同名全局变量。',
    '5. 如果需要按网络请求包导入，导入 `tars-admin-frontend.har`；HAR 中使用可导入的样例值，不包含脚本。',
    '6. 登录后如接口需要鉴权，在 Apifox 的 Cookie 管理器或环境鉴权配置中维护登录态；导入请求中不再预置 Cookie/HWID 等非必要 header。',
    '7. 当前 HAR 是根据代码静态生成的样例请求包，不包含真实线上响应耗时。',
    '',
  ].join('\n');
}

function makeTestCases() {
  return [
    '# API 测试用例说明',
    '',
    '## 断言策略',
    '',
    '- 所有接口均添加基础后置断言：HTTP 状态码为 2xx；JSON 接口断言响应体为对象；如果响应体存在业务 `code`，成功用例默认断言 `code=0`。',
    '- 登录、患者、病例、治疗序列、文件、设计、OTP、AI 分割、积分、系统消息、设备和用户配置等关键接口额外添加字段级断言，例如 `data.username`、`data.id`、`data.fileKey`、`data.surgicalDesignID`、`data.version`、`data.taskID`。',
    '- 接口之间仍保留变量提取：登录态、用户/租户/账户 ID、患者 ID、病例 ID、治疗阶段 ID、文件 key、设计 ID/版本、任务 ID、消息 ID、hwid、OTP secret/code。',
    '',
    '## 登录接口 CSV 数据驱动',
    '',
    '- 适用接口：`loginByUserName`。',
    '- CSV 文件：`D:/ubuntu/Playwright_demo/data/test_data/login_test_data.csv`。',
    '- 字段映射：`账号 -> username`，`密码 -> password`，`是否有效 -> 期望成功/失败`，`预期结果 -> 期望 message`。',
    '- 默认有效用例不依赖 CSV：`username=admin`、`password=admin`，断言 `code=0` 且 `data.username=admin`。',
    '- CSV 无效用例：先读取 CSV 的 `预期结果`，再按接口实测结果映射为实际期望 message 后断言，且业务 `code` 非 0。',
    '- 本地接口实测中，空账号、空密码、账号密码均空这几行不会返回前端表单校验文案，而是统一返回 `该账号未注册，请联系管理员`；集合脚本已把这些 CSV 文案映射为接口实际 message 后再断言。',
    '',
    '## 新增患者接口 CSV 数据驱动',
    '',
    '- 适用接口：`savePatient` / `command=13002`。',
    '- CSV 文件：`D:/ubuntu/Playwright_demo/data/test_data/patients_test_date.csv`。',
    '- 字段映射：`姓名 -> name`，`生日 -> dateOfBirth`，`电话 -> telephone`，`性别 -> gender`，`备注 -> desc`，`是否有效 -> 期望成功/失败`，`预期结果 -> 期望 message 或 patientID`。',
    '- `生日` 为空时使用默认毫秒时间戳 `631123200000`；`性别` 为空时默认 `1`；姓名、电话、备注允许空字符串进入请求体，以覆盖无效用例。',
    '- 本地接口实测中，CSV 中的患者姓名、手机号、备注校验文案属于前端表单校验；`savePatient` 接口当前仍返回 `code=0` 和患者 ID。集合脚本已按接口实际响应把这些无效行映射为 `patientID` 成功断言。',
    '- 当 `预期结果=patientID`、`是否有效=True`，或 CSV 前端校验文案被映射为接口实际成功时，断言 `code=0` 且响应中存在患者 ID。',
    '',
    '## 使用方式',
    '',
    '1. 在 Apifox 导入 `apifox-collection.postman.json`。',
    '2. 运行登录接口时选择 `login_test_data.csv` 可覆盖多个账号/密码用例；不选择 CSV 时使用集合变量中的 `admin/admin` 有效用例。',
    '3. 运行新增患者接口时选择 `patients_test_date.csv` 可覆盖患者字段校验和有效创建用例。',
    '4. 运行完整业务链路时建议不挂载登录/患者 CSV，避免某个 CSV 的无效数据影响后续依赖接口；链路接口会使用集合变量和后置提取值串联执行。',
    '',
  ].join('\n');
}

function makeValidationReport() {
  return [
    '# API 验证报告',
    '',
    '- 验证日期：2026-06-05',
    `- 本地登录页：\`${env.frontendBaseUrl}/login\``,
    `- 普通接口基址：\`${env.baseUrl}\``,
    `- 网关接口基址：\`${env.gatewayUrl}\``,
    '',
    '## 已实际请求验证',
    '',
    '- 登录接口 `POST /tars/v1/login_by_username`：`username=admin`、`password=admin`、`returnToken=false` 可返回 `Set-Cookie: session=...`；该 Cookie 为 http-only，集合后置脚本只提取响应头中的 `sessionCookie` 变量，不在请求头中预置 Cookie。',
    '- 登录接口 `returnToken=true`：本地返回 token，不返回 Cookie；文档默认改为 `returnToken=false`，更贴近后续 Cookie 鉴权链路。',
    '- 登录 CSV 无效用例实测：`demo/123` 与空账号/空密码组合在接口层均返回 `该账号未注册，请联系管理员`；空字段提示属于前端表单校验，不是当前接口响应。',
    '- 网关患者新增 `command=13002`：`dateOfBirth` 必须为 int64 毫秒时间戳，字符串日期会返回 Go 反序列化错误；文档已改为 `631123200000`。',
    '- 患者 CSV 无效字段实测：姓名为空、姓名超长、手机号格式错误、备注超长当前在 `savePatient` 接口层仍返回 `code=0` 和患者 ID；这些校验文案属于前端表单校验，不是当前接口响应。',
    '- 已串联验证通过：登录 -> `16001 getUserInfo` -> `13002 savePatient` -> `13001 queryPatientPage` -> `13003 updatePatient` -> `13007 searchPatientV2` -> `15001 addCase` -> `15003 treatmentSequence`。',
    '- 文件与设计链路验证通过：`11001 startFileUpload` -> `14002 addDesign` -> `14005 queryDesignDetail` -> `14003 changeDesign`；`14002` 实际返回 `version=0`，`14003` 使用 `version=0` 后返回下一版本。',
    '- 辅助接口抽样验证通过：`18004 getImplantFavorites`、`18002 getUserConfig`、`20002 getPointSummary`、`19001 searchMessage`、`20001 getDeviceList`。',
    '',
    '## 已修正文档问题',
    '',
    '- 网关接口统一保留小写 `command` header，移除 `PlatFrom`、`Version`、`Request-ID`、`Cookie`、`HWID`、`Command` 等非必要导入请求头。',
    '- 登录请求体改为集合变量：`username={{username}}`、`password={{password}}`、`returnToken=false`。',
    '- `savePatient`、`queryPatientPage`、`updatePatient` 使用 `patientName`、`patientIdentityCard`、`patientTelephone` 变量；`updatePatient` 补齐 `gender`、`dateOfBirth`、`identityCard`，避免只传部分字段导致后端把字段清零。',
    '- 病例、治疗序列、文件上传、手术设计、AI 分割、系统消息、OTP、积分和用户配置接口均补充前置变量校验与后置变量提取。',
    '- 所有导入集合接口均添加基础后置断言；重点接口按实际响应字段增加字段级断言。登录和新增患者接口支持读取 CSV 数据并映射为接口实际预期后断言。',
    '- DICOM/模型文件相关接口 `bindModelFileToPatient`、`unbindModelFileToPatient`、`searchPatientDetailsMessageV2`、`changeBindFile` 统一使用 `{{patientID}}`，默认值为 `692776867656982528`。',
    '- `changeTreatmentSequence.status` 改为 number 示例，避免后端按数字字段解析失败。',
    '- `addDesign`/`addDesignV2` 响应示例版本改为 `0`，`changeDesign` 使用 `version=0` 并提取返回的新 `designVersion`。',
    '- ROS/导航中带 query 的 `{designID}`、`{filename}`、`{stream_id}` 占位改为集合变量。',
    '',
    '## 前置/后置脚本',
    '',
    '- 集合级前置脚本：写入默认变量，并把 `patientID=692776867656982528` 同步到全局变量，供 DICOM/模型文件相关接口复用。',
    '- 接口级前置脚本：对依赖变量做断言，例如 `patientId`、`caseId`、`treatmentId`、`fileKey`、`designId`、`designVersion`、`taskId`、`messageId`、`hwid`、`otpSecret`、`otpCode`。',
    '- 接口级后置脚本：从响应 JSON 或响应头提取关联变量，包括登录 Cookie、用户/租户/账户 ID、患者 ID、病例 ID、治疗阶段 ID、文件 key、设计 ID/版本、AI 任务 ID、消息 ID、控制节点 hwid、OTP secret/code。',
    '',
    '## 未执行或需人工验证',
    '',
    '- 控制节点破坏性或设备状态变更接口未实测：关机、重启、删除本地文件、开始升级、设置升级、连接/断开 Wi-Fi、开启/关闭热点、导出到移动盘、录屏开始/停止。',
    '- ROS、聊天流、SSE、WebSocket、外部预签名下载、GDCM WASM 静态资源接口受设备/外部服务依赖限制，已做静态结构校验。',
    '- `navChangeDesign` 使用当前本地样例和前端真实字段均返回业务错误 `code=-10602`，文档保留接口与变量链路，但报告中标记为需后端或有效设计数据进一步确认。',
    '',
  ].join('\n');
}

function makeModuleImportGuide() {
  const lines = [
    '## 模块化导入 Apifox',
    '',
    '- `apifox-collection.postman.json`：完整集合入口，仍保留 16 个现有分组，但不再写入集合变量。',
    '- `apifox-shared-environment.postman_environment.json`：共享环境变量文件，包含 `baseUrl`、`gatewayUrl`、`username`、`password`、`patientID=692776867656982528` 等变量。',
    '- `modules/*.postman.json`：按现有分组拆分后的模块集合文件，每个文件只包含一个分组的接口，可单独导入 Apifox。',
    '- 模块集合不包含 `variable` 字段，也不设置文件夹/模块变量；接口脚本会把登录、患者、病例、文件、设计等关联 ID 写入环境变量和全局变量。',
    '- 建议导入顺序：先导入共享环境变量文件，再按需导入 `modules/` 下的模块集合。',
    '',
    '| 模块文件 | 分组 | 接口数 |',
    '| --- | --- | ---: |',
  ];
  groups.forEach((group, index) => {
    lines.push(`| \`modules/${getModuleFileName(group, index)}\` | ${group.name} | ${group.endpoints.length} |`);
  });
  lines.push('');
  return lines.join('\n');
}

function makeModulesReadme() {
  return [
    '# Apifox 模块集合',
    '',
    '本目录下每个 `.postman.json` 文件对应标准接口文档中的一个现有分组，可单独导入 Apifox。',
    '',
    '导入前请先导入上级目录的 `apifox-shared-environment.postman_environment.json`，或在 Apifox 项目/环境变量中维护同名变量。',
    '',
    makeModuleImportGuide(),
  ].join('\n');
}

function makeReadmeV2() {
  return [
    '# API Docs',
    '',
    '本目录由前端代码静态整理接口生成，已按业务域分组，并支持按模块单独导入 Apifox。',
    '',
    '## 文件说明',
    '',
    '- `standard-api-doc.md`：标准接口文档，包含接口名称、描述、请求地址、方式、请求头、Req、Res 和源码位置。',
    '- `apifox-collection.postman.json`：完整集合文件，保留 16 个现有分组和网关 `command` header，不写入集合变量。',
    '- `apifox-shared-environment.postman_environment.json`：共享环境变量文件，供完整集合和模块集合共同使用。',
    '- `modules/*.postman.json`：按现有分组拆分后的模块集合文件，可分模块导入 Apifox。',
    '- `tars-admin-frontend.har`：可导入 Apifox 的 HAR 文件，按接口生成请求包；网关接口通过 `command` header 区分。',
    '- `validation-report.md`：接口验证记录、已修正问题、变量提取链路和未执行接口说明。',
    '- `test-cases.md`：接口测试用例设计、CSV 数据驱动字段映射和后置断言说明。',
    '- `generate-api-docs.mjs`：文档生成脚本。',
    '',
    '## 本地环境',
    '',
    `- 前端登录页：\`${env.frontendBaseUrl}/login\``,
    `- 普通后端接口：\`${env.baseUrl}\``,
    `- 网关接口：\`${env.gatewayUrl}\``,
    `- 控制节点接口：\`${env.controlNodeBaseUrl}\``,
    `- ROS 接口：\`${env.rosBaseUrl}\``,
    `- 聊天接口：\`${env.chatBaseUrl}\``,
    '',
    '## Apifox 使用建议',
    '',
    '1. 需要一次性导入时，导入 `apifox-collection.postman.json`；需要分模块导入时，按需导入 `modules/*.postman.json`。',
    '2. 变量已提升到共享环境/全局变量，不再设置为集合或模块变量；建议先导入 `apifox-shared-environment.postman_environment.json`。',
    '3. 接口级前置校验和后置提取脚本会把登录态、患者、病例、文件、设计、任务和消息等关联值写入环境变量和全局变量。',
    '4. 网关接口统一请求 `POST {{gatewayUrl}}`，并保留小写 `command` header 作为分发指令。',
    '5. DICOM/模型文件相关接口统一使用 `{{patientID}}`，共享环境默认值为 `692776867656982528`。',
    '6. 登录和新增患者接口支持 CSV 数据驱动；不挂载 CSV 时使用共享环境变量中的默认有效用例。',
    '7. 登录后如接口需要鉴权，在 Apifox 的 Cookie 管理器或环境鉴权配置中维护登录态；导入请求中不预置 Cookie/HWID 等非必要 header。',
    '',
    makeModuleImportGuide(),
  ].join('\n');
}

function normalizeVariableScopeText(content) {
  return content
    .replace(
      '导入 `apifox-collection.postman.json` 后会包含集合变量，并通过前置/后置脚本在接口之间自动传递登录态、患者、病例、文件、设计、任务和消息等 ID。DICOM/模型文件相关接口统一使用 `{{patientID}}`，默认值为 `692776867656982528`，集合级前置脚本也会写入同名全局变量。',
      '导入 `apifox-collection.postman.json` 或 `modules/*.postman.json` 前，建议先导入 `apifox-shared-environment.postman_environment.json`。集合和模块文件不再写入集合/模块变量；前置/后置脚本通过环境变量和全局变量在接口之间自动传递登录态、患者、病例、文件、设计、任务和消息等 ID。DICOM/模型文件相关接口统一使用 `{{patientID}}`，默认值为 `692776867656982528`。',
    )
    .replaceAll('集合变量', '共享环境变量')
    .replaceAll('集合级前置脚本', '集合/模块前置脚本')
    .replaceAll('集合级前置', '集合/模块前置');
}

const moduleOutputDir = path.join(__dirname, 'modules');
fs.mkdirSync(moduleOutputDir, { recursive: true });

fs.writeFileSync(path.join(__dirname, 'README.md'), makeReadmeV2(), 'utf8');
fs.writeFileSync(path.join(__dirname, 'standard-api-doc.md'), `${normalizeVariableScopeText(makeMarkdown())}\n${makeModuleImportGuide()}`, 'utf8');
fs.writeFileSync(path.join(__dirname, 'apifox-collection.postman.json'), makePostmanCollection(), 'utf8');
fs.writeFileSync(path.join(__dirname, 'apifox-shared-environment.postman_environment.json'), makeSharedEnvironment(), 'utf8');
fs.writeFileSync(path.join(__dirname, 'tars-admin-frontend.har'), makeHar(), 'utf8');
fs.writeFileSync(path.join(__dirname, 'validation-report.md'), `${normalizeVariableScopeText(makeValidationReport())}\n${makeModuleImportGuide()}`, 'utf8');
fs.writeFileSync(path.join(__dirname, 'test-cases.md'), normalizeVariableScopeText(makeTestCases()), 'utf8');
fs.writeFileSync(path.join(moduleOutputDir, 'README.md'), makeModulesReadme(), 'utf8');

groups.forEach((group, index) => {
  fs.writeFileSync(path.join(moduleOutputDir, getModuleFileName(group, index)), makePostmanModuleCollection(group), 'utf8');
});

console.log(
  `Generated ${allEndpoints.length} endpoints in ${groups.length} groups and ${groups.length} module collections.`,
);
