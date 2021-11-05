import sys
import os
from flask import Flask, request, abort # 引用flask套件
from flask_cors import CORS # 網站同源

# setup path
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from linebot import (LineBotApi, WebhookHandler) # 引用line套件
from linebot.exceptions import (InvalidSignatureError) # 證驗消息用的套件, 引用無效簽章錯誤
import json
import urllib.request # 圖片下載與上傳專用

import logging # 建立日誌紀錄設定檔, https://googleapis.dev/python/logging/latest/stdlib-usage.html
import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler

# 啟用log的客戶端
client = google.cloud.logging.Client()

# 建立line event log，用來記錄line event
bot_event_handler = CloudLoggingHandler(client,name="test_bot_event")
bot_event_logger=logging.getLogger('test_bot_event')
bot_event_logger.setLevel(logging.INFO)
bot_event_logger.addHandler(bot_event_handler)

# 載入基礎設定檔
secretFileContentJson=json.load(open("./line_secret_key",'r',encoding='utf8'))
# server_url=secretFileContentJson.get("server_url")
line_bot_api = LineBotApi(secretFileContentJson.get("channel_access_token")) # 專門跟line溝通
handler = WebhookHandler(secretFileContentJson.get("secret_key")) # 收消息用的

# 準備app, 設定Server啟用細節
app = Flask(__name__,static_url_path = "/img/imagemap" , static_folder = "./img/imagemap")
CORS(app)

# 設定機器人訪問入口, http的入口, 讓line傳消息用的
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature'] # get X-Line-Signature header value

    body = request.get_data(as_text=True) # get request body as text
    # print(body)
    bot_event_logger.info(body) # 消息整個交給bot_event_logger，請它傳回GCP

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

# 引用會用到的套件
from linebot.models import (ImagemapSendMessage,TextSendMessage,ImageSendMessage,LocationSendMessage,FlexSendMessage,VideoSendMessage,StickerSendMessage,AudioSendMessage)
from linebot.models.template import (ButtonsTemplate,CarouselTemplate,ConfirmTemplate,ImageCarouselTemplate)
from linebot.models import *

# 引用套件
from linebot.models import (
    FollowEvent, UnfollowEvent
)
from models.user import User
from google.cloud import storage
from daos.user_dao import UserDAO
from utils.reply_send_message import detect_json_array_to_new_message_array

# 關注事件處理
@handler.add(FollowEvent)
def process_follow_event(event):
    line_user_profile = line_bot_api.get_profile(event.source.user_id)

    # 將個資轉換成user
    user = User(
        line_user_id=line_user_profile.user_id,
        line_user_pic_url=line_user_profile.picture_url,
        line_user_nickname=line_user_profile.display_name,
        line_user_status=line_user_profile.status_message,
        line_user_system_language=line_user_profile.language,
        blocked=False
    )

    if user.line_user_pic_url is not None:
        # 跟line 取回照片，並放置在本地端
        file_name = user.line_user_id + '.jpg'
        urllib.request.urlretrieve(user.line_user_pic_url, file_name)

        # 上傳至bucket
        storage_client = storage.Client()
        bucket_name = "gcp-ai-linebot-skye"
        destination_blob_name = f'{user.line_user_id}/user_pic.png'
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(file_name)

        # 更新回user的圖片連結
        destination_url = f'https://storage.googleapis.com/{bucket_name}/{user.line_user_id}/user_pic.png'
        user.line_user_pic_url = destination_url

        # 移除本地檔案
        os.remove(file_name)
    
    # 存入資料庫
    UserDAO.save_user(user)
    
    # 準備回復用戶的
    result_message_array =[]  # 讀取並轉換
    replyJsonPath = "img/follow.json"
    result_message_array = detect_json_array_to_new_message_array(replyJsonPath)
    result_message_array[0].text = f'{user.line_user_nickname} {result_message_array[0].text}'
    # print(result_message_array)
    
    # 消息發送
    line_bot_api.reply_message(
        event.reply_token,
        result_message_array
    )
    
    linkRichMenuId = open('img/rich_menu/rich_menu_id', 'r').read()
    line_bot_api.link_rich_menu_to_user(event.source.user_id,linkRichMenuId)

@handler.add(UnfollowEvent)
def line_user_unfollow(event):
    user = UserDAO.get_user(event.source.user_id)
    user.blocked = True
    UserDAO.save_user(user)
    pass


# 引用套件
from linebot.models import (
    MessageEvent, TextMessage
)
from utils.combine_json import combine_carousel_json, combine_flex_carousel_json, combine_tour_card_json

import codecs
def write_json(filename,object_dict):
    # data_array:list
    data_array=[]
    json_object = json.dumps(object_dict, ensure_ascii=False, indent=4)
    data_array.append(json_object)
    with codecs.open(filename, 'w',encoding='utf-8') as f:
        content = ', '.join(data_array)
        # content = '[' + content + ']'
        f.write(content)

# 文字消息處理
@handler.add(MessageEvent,message=TextMessage)
def process_text_message(event):
    
    user = UserDAO.get_user(event.source.user_id)
    # 上傳至bucket
    storage_client = storage.Client()
    bucket_name = "gcp-ai-linebot-skye"
    bucket = storage_client.bucket(bucket_name)

    test_filename = f'{user.line_user_id}/view_list/list_nums.txt'
    if storage.Blob(bucket=bucket, name=test_filename).exists(storage_client):
        # 如果view_list資料中有list_nums.txt, 則繼續新增tour_list
        blob = bucket.get_blob(test_filename)
        list_nums = int(blob.download_as_text())+1
        # blob.delete()
        # with open('list_nums.txt','w', encoding='utf8') as f:
        #     f.write(list_nums)
        # blob.upload_from_filename('list_nums.txt')
        blob.delete()
    else:
        # 如果view_list資料中沒有list_nums.txt,, 則從本地新增txt
        list_nums = 1

    # 讀取本地檔案，並轉譯成消息
    templateArray = combine_carousel_json('img/carousel_reply_template.json',"img/website_json/"+event.message.text+"_website.json",event.message.text)
    # 修改templateArray中的data
    for v in templateArray[0]['template']['columns']:
        #print(v['data'][v['data'].find('/')+1:]) #檔名
        file_name = v['data'][v['data'].find('/')+1:v['data'].find('&')]
        write_json(file_name,[v])
        if storage.Blob(bucket=bucket, name=file_name).exists(storage_client):
            pass
        else:
            # 如果view_list資料中沒有存在這個Json file, 則繼續新增view_list
            destination_blob_name = f'{user.line_user_id}/view_list/{file_name}'
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(file_name)
            # 移除本地檔案
            os.remove(file_name)
        list_nums+=1
    
    blob = bucket.blob(test_filename)
    with open('list_nums.txt','w', encoding='utf8') as f:
        f.write(str(list_nums))
    blob.upload_from_filename('list_nums.txt')
    # 移除本地檔案
    os.remove('list_nums.txt')

    result_message_array = []
    for jsonObject in templateArray:
        result_message_array.append(TemplateSendMessage.new_from_json_dict(jsonObject))

    # 發送
    line_bot_api.reply_message(
        event.reply_token,
        result_message_array
    )

from linebot.models import (
    PostbackEvent
)

from urllib.parse import parse_qs 
from utils import storage_methods

@handler.add(PostbackEvent)
def process_postback_event(event):    
    user = UserDAO.get_user(event.source.user_id)
    # 解析postback的data，並按照data欄位判斷處理, 現有的欄位 folder, label, tag, uri
    query_string_dict = parse_qs(event.postback.data)
    print(event.postback.data)
    if 'uri' in query_string_dict: # 有uri的檔案就是已經上傳至storage的
        # 上傳至bucket
        storage_client = storage.Client()
        bucket_name = "gcp-ai-linebot-skye"
        bucket = storage_client.bucket(bucket_name)
        
        if query_string_dict['tag'][0]=='setup': # 在行程清單建立事件
            date_tour = event.postback.params['date']
            destination_blob_name =  user.line_user_id+'/'+query_string_dict['uri'][0]
            file_name = query_string_dict['uri'][0][query_string_dict['uri'][0].find('/')+1:]

            storage_methods.download_blob(bucket_name,  destination_blob_name, file_name)
            
            templateArray = combine_flex_carousel_json('img/flex_carousel_reply_template.json', file_name, date_tour)

            templateArray[0]['contents']['contents'][0]['footer']['contents'][0]['contents'][2]['action']['data'] = 'uri='+query_string_dict['uri'][0]+'&tag=finish'
            templateArray[0]['contents']['contents'][0]['footer']['contents'][0]['contents'][4]['action']['data']  = 'uri='+query_string_dict['uri'][0]+'&tag=delete'
            
            write_json('card_'+file_name, templateArray)
            # storage_methods.rename_blob(bucket_name, destination_blob_name, destination_blob_name.replace('view_list','setup_list'))
            result_message_array = detect_json_array_to_new_message_array('card_'+file_name)

            # 上傳到setup資料夾
            destination_blob_name = f'{user.line_user_id}/setup/card_{file_name}'
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename('card_'+file_name)
            # 移除本地檔案
            os.remove(file_name)
            os.remove('card_'+file_name)

        elif query_string_dict['tag'][0]=='finish': # 在行程清單建立事件
            destination_blob_name =  user.line_user_id+'/setup/card_'+query_string_dict['uri'][0][query_string_dict['uri'][0].find('/')+1:]
            storage_methods.rename_blob(bucket_name, destination_blob_name, destination_blob_name.replace('setup','finish'))

            result_message_array =[]  # 讀取並轉換
            replyJsonPath = "img/finish_card.json"
            result_message_array = detect_json_array_to_new_message_array(replyJsonPath)

        elif query_string_dict['tag'][0]=='delete': # 在行程清單建立事件
            destination_blob_name =  user.line_user_id+'/setup/card_'+query_string_dict['uri'][0][query_string_dict['uri'][0].find('/')+1:]
            blob = bucket.blob(destination_blob_name)
            blob.delete()

            result_message_array =[]  # 讀取並轉換
            replyJsonPath = "img/delete_card.json"
            result_message_array = detect_json_array_to_new_message_array(replyJsonPath)
        
        # 發送
        line_bot_api.reply_message(
            event.reply_token,
            result_message_array
        )

    if 'tag' in query_string_dict and 'uri' not in query_string_dict: # 
        if query_string_dict['tag'][0] == "推薦行程":
            result_message_array =[]  # 讀取並轉換
            replyJsonPath = "img/推薦行程.json"
            result_message_array = detect_json_array_to_new_message_array(replyJsonPath)

        elif query_string_dict['tag'][0] == "自由行":
            result_message_array =[]  # 讀取並轉換
            replyJsonPath = "img/待建.json"
            result_message_array = detect_json_array_to_new_message_array(replyJsonPath)

        elif query_string_dict['tag'][0] == "跟團":
            result_message_array =[]  # 讀取並轉換
            replyJsonPath = "img/待建.json"
            result_message_array = detect_json_array_to_new_message_array(replyJsonPath)

        elif query_string_dict['tag'][0] == "建立行程":
            result_message_array =[]  # 讀取並轉換
            replyJsonPath = "img/建立行程.json"
            result_message_array = detect_json_array_to_new_message_array(replyJsonPath)

        elif query_string_dict['tag'][0] == "操作說明":
            result_message_array =[]  # 讀取並轉換
            replyJsonPath = "img/操作說明.json"
            result_message_array = detect_json_array_to_new_message_array(replyJsonPath)

        elif query_string_dict['tag'][0] == "查詢清單":
            storage_client = storage.Client()
            bucket_name = "gcp-ai-linebot-skye"
            blobs = storage_client.list_blobs(bucket_name)

            blobs = storage_client.list_blobs(bucket_name,prefix=f'{user.line_user_id}/setup/', delimiter=True)
            file_name=[]
            for blob in blobs:
                file_name.append(blob.name[blob.name.find('card'):])
                storage_methods.download_blob(bucket_name,  blob.name, blob.name[blob.name.find('card'):])
            if file_name:
                templateArray = combine_tour_card_json(file_name)                
                write_json('查詢清單.json', templateArray)

                result_message_array =[]  # 讀取並轉換
                replyJsonPath = "查詢清單.json"
                result_message_array = detect_json_array_to_new_message_array(replyJsonPath)
                
                for f in file_name:
                    os.remove(f)
                os.remove("查詢清單.json")
            else:
                result_message_array =[]  # 讀取並轉換
                replyJsonPath = "img/空查詢.json"
                result_message_array = detect_json_array_to_new_message_array(replyJsonPath)

        elif query_string_dict['tag'][0] == "歷史旅程":
            storage_client = storage.Client()
            bucket_name = "gcp-ai-linebot-skye"
            blobs = storage_client.list_blobs(bucket_name)

            blobs = storage_client.list_blobs(bucket_name,prefix=f'{user.line_user_id}/finish/', delimiter=True)
            file_name=[]
            for blob in blobs:
                file_name.append(blob.name[blob.name.find('card'):])
                storage_methods.download_blob(bucket_name,  blob.name, blob.name[blob.name.find('card'):])

            if file_name:
                templateArray = combine_tour_card_json(file_name)                
                write_json('歷史旅程.json', templateArray)

                result_message_array =[]  # 讀取並轉換
                replyJsonPath = "歷史旅程.json"
                result_message_array = detect_json_array_to_new_message_array(replyJsonPath)
                
                for f in file_name:
                    os.remove(f)
                os.remove("歷史旅程.json")
            else:
                result_message_array =[]  # 讀取並轉換
                replyJsonPath = "img/空歷史.json"
                result_message_array = detect_json_array_to_new_message_array(replyJsonPath)
        # 發送
        line_bot_api.reply_message(
            event.reply_token,
            result_message_array
        )


# 運行在8080port
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))