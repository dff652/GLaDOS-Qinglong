# CLAUDE.md

GLaDOS 机场自动签到脚本，主要部署在「青龙面板」定时运行，也支持本地测试。核心逻辑全部在单文件 `glados_sign_in.py` 中。

## 运行与测试

本地使用 venv（已在仓库根目录创建，`venv/` 已被 git 忽略）：

```bash
./venv/bin/python glados_sign_in.py        # 运行签到
./venv/bin/python -m py_compile glados_sign_in.py   # 语法检查
```

依赖：`requests`、`pandas`、`python-dotenv`。本地通过根目录 `.env` 注入环境变量（`load_dotenv()`），青龙面板则在「环境变量」中配置。

## 环境变量

| 变量 | 必要 | 说明 |
|---|---|---|
| `GLADOS_COOKIE` | 是 | 账号 Cookie，多个账号用 `&` 分隔，每个 cookie 结尾带 `;` |
| `PUSHPLUS_TOKEN` | 否 | pushplus 推送 token，留空则不推送 |
| `WEBHOOK_CODE` | 否 | pushplus webhook 编码，留空则用微信公众号渠道 |
| `GLADOS_ORIGIN` | 否 | 站点域名。**手动配置的优先**，全部不通再回退到内置镜像（`DEFAULT_ORIGINS`：space/network/rocks/one/cloud）；`ORIGINS` 由二者合并去重保序得到，按序故障转移到第一个连通的。可逗号分隔（结尾不带斜杠） |
| `GLADOS_TOKEN` | 否 | 签到接口 payload token，默认 `glados.cloud` |

## 代码约定

- 网络请求分两层：`request_with_retry(method, url, headers, data, label, max_retries)` 是带超时（`REQUEST_TIMEOUT`=15s）+ 重试的底层封装；`request_with_failover(method, path, cookie, payload, label)` 在其上做多域名故障转移并缓存命中域名（`_active_origin`）。新增 GLaDOS 接口请求走 `request_with_failover`（传 path 而非完整 URL），二者全部失败均返回 `None`，调用方需判空。
- 多域名时每个域名只试 `ORIGIN_ATTEMPTS`=1 次（靠切换域名容错）；单域名时退回 `MAX_RETRIES`=3 次重试。
- URL 由 `request_with_failover` 内按 `{origin}{path}` 派生，切换域名只改 `GLADOS_ORIGIN`，不要硬编码域名。
- `start()` 内的 per-account 循环开头会初始化 `points`/`message_status`/`change` 等变量，避免异常路径下 `NameError`；新增账号级字段也应在此处给默认值。

## 安全注意

- `.env` 与 `.env.example` 不得包含真实密钥/Cookie；模板只用占位符。仓库历史中曾出现过真实 pushplus token，改动凭据相关内容时务必谨慎。
