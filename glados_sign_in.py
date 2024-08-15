import requests,json,os

# pushplus秘钥
sckey = os.environ.get("PUSHPLUS_TOKEN", "")

# glados账号cookie
cookies= os.environ.get("GLADOS_COOKIE", []).split("&")
if cookies[0] == "":
    print('未获取到COOKIE变量') 
    cookies = []
    exit(0)




def start():   
    # 推送内容
    title = "GLaDOS"
    success, fail = 0, 0        # 成功账号数量 失败账号数量
    sendContent = ""


    url= "https://glados.rocks/api/user/checkin"
    url2= "https://glados.rocks/api/user/status"
    referer = 'https://glados.rocks/console/checkin'
    origin = "https://glados.rocks"
    useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
    payload={
        'token': 'glados.one'
    }
    for cookie in cookies:
        checkin = requests.post(url,headers={'cookie': cookie ,'referer': referer,'origin':origin,'user-agent':useragent,'content-type':'application/json;charset=UTF-8'},data=json.dumps(payload))
        state_response =  requests.get(url2,headers={'cookie': cookie ,'referer': referer,'origin':origin,'user-agent':useragent})
    #--------------------------------------------------------------------------------------------------------#  
        state = state_response.json()
        leftdays = str(state['data']['leftDays']).split('.')[0]
        email = state['data']['email']

        if checkin.status_code == 200:
            checkin_result = checkin.json()
            message_status = checkin_result['message']

            print(email+'----'+message_status+'----剩余('+leftdays+')天')

            if "Checkin" in message_status:
                success += 1
                message_content = "签到成功，会员天数 + 1"

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
            签到状态: {message_content}\n\
            签到消息：{message_status}\n\
            状态码：{checkin.status_code}\n\
            剩余天数: {message_days}\n"
        
        if cookie == cookies[-1]:
            sendContent += '-' * 30

    #--------------------------------------------------------------------------------------------------------#   
    print("sendContent:" + "\n", sendContent)

    if sckey != "":
        title += f': 成功{success},失败{fail}'
        
        url = 'http://www.pushplus.plus/send'
        data = {
            "token":sckey,
            "title":title,
            "content":sendContent,
            "channel":"webhook",
            "webhook":"设置自定义的webhook编码"
        }
        
        body=json.dumps(data).encode(encoding='utf-8')
        headers = {'Content-Type':'application/json'}
        requests.post(url,data=body,headers=headers)

def main_handler(event, context):
  return start()

if __name__ == '__main__':
    start()