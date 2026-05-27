# GLaDOS 自动签到脚本

## 更新日志

### 2026-05-27
- ✨ **域名可配置**: 新增 `GLADOS_ORIGIN` 环境变量，可自定义站点域名以应对默认域名需科学上网的情况
- ✨ **多域名故障转移**: `GLADOS_ORIGIN` 支持逗号分隔多个候选域名，按顺序尝试并自动切到第一个连通的域名
- ✨ **内置镜像域名**: 内置 space/network/rocks/one/cloud 五个镜像作为后备；手动配置的域名优先，全部不通时自动回退到内置域名，零配置即可自动切换到可直连域名
- ✨ **切换日志**: 故障转移过程输出明确日志，标注当前域名来源（手动/内置/复用）、切换原因与回退时机
- ✨ **token 可配置**: 新增 `GLADOS_TOKEN` 环境变量（默认 `glados.cloud`）
- 🐛 **健壮性修复**: 修正 `GLADOS_COOKIE` 未设置时的崩溃；为推送请求添加超时；域名返回非 JSON（拦截页/维护页）时不再整体崩溃，改为优雅跳过

### 2026-01-07
- ✨ **域名更换**: API 地址从 `glados.rocks` 更新为 `glados.space`
- ✨ **重试机制**: 新增请求超时（15秒）和自动重试（最多3次）功能
- ✨ **本地测试支持**: 支持 `.env` 文件配置环境变量（需安装 `python-dotenv`）
- ✨ **错误处理优化**: 改进 Cookie 无效时的错误提示信息
- 🐛 **修复 pushplus 推送**: 兼容无 webhook 配置的情况，未配置 webhook 时自动使用微信公众号推送
- 🐛 **修复数据解析**: 增强签到返回数据的验证，处理数据为空或格式不完整的情况

## 依赖安装

```bash
pip install requests pandas python-dotenv
```

## 青龙面板部署

1. **自动添加**：订阅管理中创建订阅，复制仓库链接 https://github.com/dff652/GLaDOS-Qinglong.git  
   **手动添加**：下载脚本文件 `glados_sign_in.py`，在青龙面板的脚本管理中添加脚本
2. **设置环境变量**：
   - `GLADOS_COOKIE`（必要）：多个账号使用 `&` 隔开，示例：`cookie1;&cookie2`，每个 cookie 结尾后要加上 `;`
   - `PUSHPLUS_TOKEN`（非必要）
   - `WEBHOOK_CODE`（参考 pushplus 设置教程）
   - `GLADOS_ORIGIN`（非必要）：站点域名。**使用原则**——手动填写的域名优先尝试，全部不通时自动回退到脚本**内置的镜像域名**（space/network/rocks/one/cloud）。因此不填也能用：脚本会自动逐个尝试、用第一个能连通的，无需手动配置即可应对默认域名需科学上网的情况。仅当你有专属镜像或想优先指定某域名时才配置，可逗号分隔多个（结尾不带斜杠）
   - `GLADOS_TOKEN`（非必要）：签到接口 token，默认 `glados.cloud`，一般无需修改
3. 添加定时任务，设置命令和定时规则

## 本地测试

1. 复制 `.env.example` 为 `.env`
2. 填写你的真实 Cookie 值（**不要加引号**）
3. 运行脚本：`python glados_sign_in.py`

## pushplus 设置流程

> 💡 **说明**：如果不配置 `WEBHOOK_CODE`，将使用默认的微信公众号推送方式。

1. 注册 [pushplus](https://www.pushplus.plus/) 获取自己的 token
2. （可选）如需使用 webhook 渠道（如钉钉机器人），参考 https://www.pushplus.plus/doc/extend/webhook.html
3. （可选）配置好钉钉机器人后设置 `WEBHOOK_CODE` 环境变量

## 效果展示

![image](https://github.com/user-attachments/assets/989166a8-9699-4841-ba53-a0935a98a747)




# 参考项目：
1. https://github.com/Devilstore/Gladoscheckin
2. https://github.com/domeniczz/GLaDOS_checkin_auto
