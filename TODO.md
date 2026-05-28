# 待办

## 1. 代理支持（应对网络完全无法访问 GLaDOS 的情况）★ 重要

**背景**：2026-05-27 实测，在某无法科学上网的部署网络里，GLaDOS 全部 6 个域名
（手动 glados.space + 内置 network/rocks/one/cloud）**全部超时**，耗时 151s 全失败。

**结论**：这是**网络出口**问题，不是域名选择问题——再加多少候选域名都无效，
也无法"自动发现"可达域名（出口被卡死时探测只会更慢）。多域名故障转移只在
"至少有一个 GLaDOS 域名可达"时才有意义。

**真正的解法（按优先级）**：
- [ ] **给脚本加代理支持**：新增 `GLADOS_PROXY` 环境变量（或读取标准 `HTTPS_PROXY`），
      通过 `requests(..., proxies=...)` 把请求经代理转发。前提：青龙宿主机能访问到某个
      可达 GLaDOS 的代理（本地 clash/v2ray 端口、或外部 http/socks5 代理）。
- [ ] 备选：把青龙部署到墙外 VPS（无需改代码）。
- [ ] 弱备选：DoH 解析真实 IP——仅当"DNS 污染但 IP 未被墙"才有效，不稳定。

## 2. "今日已签到"文案误判（已知，待修）

GLaDOS 返回 `Today's observation logged. Return tomorrow for more points.` 时，
匹配逻辑（`glados_sign_in.py` 中 `if "Points" in message_status / "Please Try Tomorrow"`）
两者都不命中 → 误判为"签到失败"。
- [ ] 改用接口返回的 `code` 字段判断成功/失败，或放宽文案匹配（忽略大小写 / 识别 `observation logged`）。

## 3. 故障转移是否覆盖 HTTP 错误（待定）

当前 `request_with_failover` 只在网络异常（超时/连接失败）时切换域名；
域名返回 403/5xx/拦截页（HTTP 层有响应）会被当作"成功"而停止切换并缓存。
- [ ] 评估是否让 403/5xx 也触发切换到下一个域名（注意：会改变现有 502 的处理路径）。

## 4. 清理 git 历史中的真实凭据（安全）

更早的提交历史里存在真实的 pushplus token。
- [ ] 如在意，用 `git filter-repo` 重写历史并 force push（会改变 commit hash）。
- [ ] 并在 pushplus 后台重置该 token。
