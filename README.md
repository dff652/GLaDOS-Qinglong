# 青龙面板部署
1. 自动添加：订阅管理中创建订阅，复制仓库链接 https://github.com/dff652/GLaDOS-Qinglong.git  手动添加：下载脚本文件glados_sign_in.py，在青龙面板的脚本管理中添加脚本
2. 设置环境变量：GLADOS_COOKIE（必要） ， PUSHPLUS_TOKEN（非必要）， WEBHOOK_CODE（参考pushplus设置教程）。如GLADOS_COOKIE多个账号需使用 '&' 隔开，示例：cookie&cookie
3. 添加定时任务，设置命令和定时规则

# pushplus 设置流程
1. 注册pushplus获取自己的token
2. 配置webhook渠道，如钉钉机器人等，参考 https://www.pushplus.plus/doc/extend/webhook.html#%E4%BD%BF%E7%94%A8%E6%AD%A5%E9%AA%A4
3. 配置好钉钉机器人后设置webhook编码

# 参考项目：
1. https://github.com/Devilstore/Gladoscheckin
2. https://github.com/domeniczz/GLaDOS_checkin_auto
