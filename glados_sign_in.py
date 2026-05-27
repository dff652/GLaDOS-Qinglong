import requests,json,os
import datetime
import pandas as pd
import time
from dotenv import load_dotenv
load_dotenv()

# 请求超时时间（秒）
REQUEST_TIMEOUT = 15
# 最大重试次数
MAX_RETRIES = 3


# pushplus秘钥
sckey = os.environ.get("PUSHPLUS_TOKEN", "")

# glados账号cookie
cookies= os.environ.get("GLADOS_COOKIE", "").split("&")

# webhook编码
webhook_code = os.environ.get("WEBHOOK_CODE", "")

# GLaDOS 内置候选域名（均指向同一套 API 的镜像，2026-05 实测可用），作为后备
DEFAULT_ORIGINS = ["https://glados.space", "https://glados.network",
                   "https://glados.rocks", "https://glados.one", "https://glados.cloud"]

def _parse_origins(raw):
    return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]

# 域名使用原则：环境变量 GLADOS_ORIGIN 手动配置的优先尝试，全部不通再自动回退到内置域名。
# 合并去重并保序，因此手动域名永远排在内置域名之前；不配置时仅用内置域名。
MANUAL_ORIGINS = _parse_origins(os.environ.get("GLADOS_ORIGIN", ""))
ORIGINS = list(dict.fromkeys(MANUAL_ORIGINS + DEFAULT_ORIGINS))
# 多域名时每个域名只试 1 次，靠切换域名容错（快速切换）；仅剩单域名才退回完整重试
ORIGIN_ATTEMPTS = 1 if len(ORIGINS) > 1 else MAX_RETRIES
_active_origin = None   # 缓存首个成功的域名，后续请求/账号优先复用

# 浏览器 UA，请求头复用
USERAGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"

# 签到接口 payload 中的 token（可在青龙面板配置 GLADOS_TOKEN，随域名/站点变化时切换）
checkin_token = os.environ.get("GLADOS_TOKEN", "glados.cloud")

# 测试格式
# sckey = ""
# webhook_code = ""
# cookie_str = ""
# cookies = cookie_str.split("&")

if cookies[0] == "":
    print('未获取到COOKIE变量') 
    cookies = []
    exit(0)

def request_with_retry(method, url, headers, data=None, label="请求", max_retries=MAX_RETRIES):
    """带超时和重试的 HTTP 请求；全部重试失败返回 None"""
    for attempt in range(max_retries):
        try:
            print(f"尝试{label} (第 {attempt + 1}/{max_retries} 次)...")
            resp = requests.request(method, url, headers=headers, data=data, timeout=REQUEST_TIMEOUT)
            print(f"{label}请求成功，状态码: {resp.status_code}")
            return resp
        except requests.exceptions.Timeout:
            print(f"{label}请求超时 (第 {attempt + 1} 次)")
        except requests.exceptions.RequestException as e:
            print(f"{label}请求异常: {e}")
        if attempt < max_retries - 1:
            print("等待 3 秒后重试...")
            time.sleep(3)
    return None


def request_with_failover(method, path, cookie, payload=None, label="请求"):
    """依次尝试各候选域名（手动优先、内置后备），命中即缓存供后续复用；全部失败返回 None。
    日志会说明每次在试哪类域名、为何切换、何时回退到内置域名。"""
    global _active_origin

    def _try(origin, source):
        print(f"[{label}] ▶ 尝试域名：{origin}（{source}）")
        headers = {
            'cookie': cookie,
            'referer': f"{origin}/console/checkin",
            'origin': origin,
            'user-agent': USERAGENT,
        }
        data = None
        if payload is not None:
            headers['content-type'] = 'application/json;charset=UTF-8'
            data = json.dumps(payload)
        return request_with_retry(method, f"{origin}{path}", headers, data=data,
                                  label=label, max_retries=ORIGIN_ATTEMPTS)

    # 1) 优先复用上次成功的域名，避免每次都从头探测
    if _active_origin in ORIGINS:
        resp = _try(_active_origin, "复用上次可用域名")
        if resp is not None:
            return resp
        print(f"[{label}] ✗ 上次可用域名 {_active_origin} 这次不通，转为重新探测全部候选域名…")

    # 2) 按「手动优先、内置后备」依次尝试
    fell_back = False
    for origin in ORIGINS:
        if origin == _active_origin:
            continue  # 已在上一步试过，跳过
        is_builtin = origin not in MANUAL_ORIGINS
        # 首次从手动域名跨入内置域名时，明确提示「回退」原因
        if is_builtin and MANUAL_ORIGINS and not fell_back:
            print(f"[{label}] ↪ 手动配置的域名全部不通，自动回退到内置镜像域名继续尝试")
            fell_back = True
        resp = _try(origin, "内置后备" if is_builtin else "手动配置")
        if resp is not None:
            if _active_origin != origin:
                print(f"[{label}] ✅ 域名 {origin} 可用，本次及后续请求将优先使用它")
            _active_origin = origin
            return resp
        print(f"[{label}] ✗ {origin} 不可用（请求失败/超时），切换下一个候选域名…")

    print(f"[{label}] ✗ 全部候选域名均不可用（手动 {len(MANUAL_ORIGINS)} 个 + 内置 {len(DEFAULT_ORIGINS)} 个）")
    return None


def calculate_consecutive_days(dataframe):
    """
    计算连续签到天数
    """
    df = dataframe.copy()
    interval = df['checkin_date'] -df['checkin_date'].shift(1)
    if not pd.api.types.is_timedelta64_dtype(interval):
        interval = pd.to_timedelta(interval)
    
    interval_days = abs(interval.dt.days)
    
    df['interval_days'] = interval_days.fillna(1)
    df['Group'] = (df['interval_days'] != df['interval_days'].shift()).cumsum()
    
    consecutive_days =  len(df[df['Group'] == 1])
    
    
    return consecutive_days
        
    
    

def start():   
    # 推送内容
    title = "GLaDOS"
    success, fail = 0, 0        # 成功账号数量 失败账号数量
    sendContent = ""


    payload={
        'token': checkin_token
    }
    for cookie in cookies:
        # 默认值，避免 else 分支或异常路径引用到未定义变量
        points = 0
        message_status = "未知状态"
        change = 0
        balance = 0
        checkin_time = ""
        checkin_date = ""
        consecutive_days = 0
        # 签到请求，多域名故障转移 + 重试
        checkin = request_with_failover("POST", "/api/user/checkin", cookie, payload=payload, label="签到")

        if checkin is None:
            message_content = "签到请求失败，所有重试均超时"
            fail += 1
            sendContent += f"签到状态: {message_content}\n\n"
            continue

        if checkin.status_code == 502:
            message_content = "签到请求失败，服务器返回502 Bad Gateway"
            fail += 1
            sendContent += f"签到状态: {message_content}\n\n"
            continue

        # 获取用户状态，多域名故障转移 + 重试
        state_response = request_with_failover("GET", "/api/user/status", cookie, label="获取用户状态")

        if state_response is None:
            message_content = "获取用户状态失败，所有重试均超时"
            fail += 1
            sendContent += f"签到状态: {message_content}\n\n"
            continue

        try:
            state = state_response.json()
        except ValueError:
            message_content = "获取用户状态失败：响应非 JSON（域名可能返回了拦截页/维护页）"
            print(f"⚠️ {message_content}: {state_response.text[:120]}")
            fail += 1
            sendContent += f"签到状态: {message_content}\n\n"
            continue

        # 检查返回状态：code=0 表示成功，其他值表示失败
        if state_response.status_code != 200 or state.get('code', -1) != 0:
            error_msg = state.get('message', '未知错误')
            error_code = state.get('code', '未知')
            message_content = f"获取用户状态失败 [code={error_code}]: {error_msg}"
            print(f"⚠️ Cookie 可能无效或已过期: {message_content}")
            print(f"   请重新获取 Cookie 并更新 .env 文件")
            fail += 1
            sendContent += f"签到状态: {message_content}\n\n"
            continue
    #--------------------------------------------------------------------------------------------------------#  
        leftdays = str(state['data']['leftDays']).split('.')[0]
        email = state['data']['email']
        vip_days = state['data']['vip']
        
        if checkin.status_code == 200:
            try:
                checkin_result = checkin.json()
            except ValueError:
                print(f"⚠️ 签到响应非 JSON（域名可能返回了拦截页/维护页）: {checkin.text[:120]}")
                checkin_result = {}
            message_status = checkin_result.get('message', '未知状态')
            
            # 本次执行获取的点数
            points = checkin_result.get('points', 0)
            
            # 获取签到记录
            checkin_list = checkin_result.get('list', [])
            
            # 检查签到记录是否为空或格式不完整
            if not checkin_list or not isinstance(checkin_list, list) or len(checkin_list) == 0:
                print(f"⚠️ 签到记录为空或格式异常，跳过详细统计")
                # 使用默认值
                change = 0
                balance = 0
                checkin_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                checkin_date = datetime.datetime.now().date()
                consecutive_days = 0
            else:
                # 检查必要字段是否存在
                first_record = checkin_list[0]
                required_fields = ['change', 'balance', 'time']
                missing_fields = [f for f in required_fields if f not in first_record]
                
                if missing_fields:
                    print(f"⚠️ 签到记录缺少字段: {missing_fields}，跳过详细统计")
                    change = 0
                    balance = 0
                    checkin_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    checkin_date = datetime.datetime.now().date()
                    consecutive_days = 0
                else:
                    df_checkin = pd.DataFrame(checkin_list)
                    df_checkin['change'] = df_checkin['change'].astype('float')
                    df_checkin['checkin_date'] = df_checkin['time'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000).date())
                    df_checkin['checkin_time'] = df_checkin['time'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000).strftime('%Y-%m-%d %H:%M:%S'))
                    
                    # 过滤出积分增加和签到记录，排除积分扣除记录
                    valid_checkin = df_checkin[df_checkin['change'] >= 0]
                    
                    # 本日积分变动
                    change = df_checkin['change'].iloc[0]
                    
                    # 当前剩余积分
                    balance = int(float(df_checkin['balance'].iloc[0]))
                    
                    # 执行签到的时间
                    checkin_time = df_checkin['checkin_time'].iloc[0]
                    
                    # 最近签到日期
                    checkin_date = df_checkin['checkin_date'].iloc[0]
                    
                    # 计算连续天数
                    consecutive_days = calculate_consecutive_days(valid_checkin)
            
            
            
            # # 本日签到获取点数
            # change = int(float(checkin_result['list'][0]['change']))
            
            # # 账号当前剩余活动点数
            # balance =  int(float(checkin_result['list'][0]['balance']))
            
            # # 执行签到的时间
            # checkin_timestamp = checkin_result['list'][0]['time'] /1000
            # checkin_time = datetime.datetime.fromtimestamp(checkin_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            # # 预计签到的日期
            # checkin_date = checkin_result['list'][0]['business'].split(':')[-1]
            
            # # 计算连续签到天数
            # consecutive_days = calculate_consecutive_days(checkin_result['list'])
            
            print(email+'----'+message_status+'----剩余('+leftdays+')天')

            if "Points" in message_status:
                success += 1
                message_content = "签到成功"

            elif "Please Try Tomorrow" in message_status:
                message_content = "今日已签到"

            else:
                fail += 1
                message_content = "签到失败，请检查..."

            if leftdays is not None:
                message_days = f"{leftdays} 天"

            else:
                message_days = "无法获取剩余天数信息"

        else:
            message_content = "签到请求url失败, 请检查...cookie"
            message_days = "获取信息失败"


        # 推送内容
        sendContent += f"{'-'*30}\n\
            成功：{success}\n\
            失败：{fail}\n\
            账号: {email}\n\
            状态码：{checkin.status_code}\n\
            签到状态: {message_content}\n\
            签到消息：{message_status}\n\
            本次执行获取积分：{points}\n\
            本日积分变动: {change}\n\
            剩余天数: {leftdays}\n\
            剩余VIP天数: {vip_days}\n\
            当前积分: {balance}\n\
            签到时间: {checkin_time}\n\
            最近签到日期: {checkin_date}\n\
            连续签到天数: {consecutive_days}\n"
        
        if cookie == cookies[-1]:
            sendContent += '-' * 30

    #--------------------------------------------------------------------------------------------------------#   
    print("sendContent:" + "\n", sendContent)

    if sckey != "":
        title += f': 成功{success},失败{fail}'
        
        push_url = 'http://www.pushplus.plus/send'
        data = {
            "token": sckey,
            "title": title,
            "content": sendContent,
        }

        # 只有配置了 webhook 编码时才使用 webhook 渠道，否则使用默认渠道（微信公众号）
        if webhook_code != "":
            data["channel"] = "webhook"
            data["webhook"] = webhook_code

        body = json.dumps(data).encode(encoding='utf-8')
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(push_url, data=body, headers=headers, timeout=REQUEST_TIMEOUT)
            print(f"推送结果: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"推送请求失败: {e}")

def main_handler(event, context):
  return start()

if __name__ == '__main__':
    start()
        