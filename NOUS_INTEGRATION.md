# Nous 前端集成指南

Nous 是 Ombre Brain 的新前端界面，通过 REST API 与 OB 后端集成。

## 快速开始

### 本地开发

**终端 1 - 启动 OB 后端：**
```bash
python server.py
```
OB 服务运行在 `http://localhost:8000`

**终端 2 - 启动 Nous 前端：**
```bash
cd /path/to/nous
npm run dev
```
Nous 运行在 `http://localhost:3000`

### Docker Compose（推荐）

在根项目目录执行：
```bash
docker-compose up
```

这将同时启动：
- OB 后端: http://localhost:8000
- Nous 前端: http://localhost:3000

## 部署到生产环境

详见 `/path/to/nous/DEPLOYMENT.md`

## REST API 端点

OB 为 Nous 提供的 REST API：

### 认证
```
POST /api/ombre/auth/login
Body: { "password": "..." }
Response: 设置 session cookie
```

### 获取内存列表
```
GET /api/ombre/list-buckets
Response: [{ id, name, domain, tags, created, valence, arousal, resolved }, ...]
```

### 读取内存详情
```
GET /api/ombre/read-bucket/{bucket_id}
Response: { id, content, metadata }
```

### 创建/更新内存
```
POST /api/ombre/hold
Body: { content, domain?, tags?, whisper? }
Response: { result: bucket_id }
```

### 删除/更新内存
```
POST /api/ombre/trace
Body: { bucket_id, resolved?, delete? }
Response: { result: status }
```

## 数据映射

| 功能 | 存储方式 | 标识 |
|------|--------|------|
| Diary 日记 | 内存 bucket | domain: "diary" |
| Nightlight 夜记 | 内存 bucket | tags: "whisper" |
| Memories 记忆 | 内存 bucket | domain: "moments", "about-yvine", "us", "understanding" |

## 环境变量

**Nous 需要：**
- `NEXT_PUBLIC_OMBRE_URL` - OB 的 URL
- `NEXT_PUBLIC_OMBRE_PASSWORD` - 访问密码

## 架构

```
Nous 前端
  ├─ 用户界面 (React/Next.js)
  ├─ 静态资源 (.next/static)
  └─ REST 客户端
       └─ 调用 OB 的 /api/ombre/* 端点

Ombre Brain 后端
  ├─ MCP 工具实现
  ├─ 内存管理引擎
  └─ REST API 网关
```

## 故障排除

### Nous 无法连接 OB
1. 检查 OB 是否运行在正确的端口
2. 检查防火墙设置
3. 查看浏览器控制台的网络错误

### 认证失败
- 确保密码正确
- 检查 session cookie 是否启用

### 页面无法加载
- 检查 Nous 和 OB 的启动日志
- 确保两个服务都在运行

## 扩展

添加新的 API 端点：

1. 在 `ombre-brain/server.py` 中添加 `@mcp.custom_route()` 装饰器
2. 在 `nous/src/lib/ombre-client.ts` 中创建客户端函数
3. 在 Nous 页面中调用新的 API

详见各项目的 README 文件。
