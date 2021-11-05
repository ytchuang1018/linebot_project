import json
from linebot.models.template import *
from urllib.parse import parse_qs
import codecs
import requests
from bs4 import BeautifulSoup

def combine_carousel_json(template_jsonfile, reply_jsonfile, category ):
    # 適合讀取已寫進website/XX_website.json, 將
    # 讀取本地檔案，並轉譯成消息
    with open(template_jsonfile, encoding='utf8') as f:
        templateArray = json.load(f)
    
    with open(reply_jsonfile, encoding='utf8') as f:
        jsonArray = json.load(f)

    # modify picktimer date
    import datetime

    # 獲取今天以前(-)或以後(+)幾天的日期
    def getday(n):
        today = datetime.date.today()
        oneday = today + datetime.timedelta(days=n)
        return oneday
    
    # pickup five jourlist
    from random import shuffle
    n = list(range(0,len(jsonArray)))
    shuffle(n)
    n_r = list(map(lambda e: str(e+1), n[0:5]))

    columns = []
    for f in jsonArray:
        query_string_dict = parse_qs(f['data'])
        if query_string_dict['label'][0] in n_r:
            f['actions'][0]['initial'] = f['actions'][0]['min'] = datetime.date.today().strftime('%Y-%m-%d')
            f['actions'][0]['max'] = getday(31).strftime('%Y-%m-%d')
            f['actions'][0]['data'] = 'uri=view_list/'+category+'_'+query_string_dict['label'][0]+'.json&tag=setup'
            f['data'] = 'uri=view_list/'+category+'_'+query_string_dict['label'][0]+'.json&tag=view'
            columns.append(f)

    templateArray[0]['template']['columns'] = columns
    
    return templateArray


def combine_tour_card_json(reply_jsonfiles): # input multiple cardXX.json file
    data=[]
    for n in range(len(reply_jsonfiles)):
        with open(reply_jsonfiles[n], encoding='utf8') as f:
            jsonArray = json.load(f)
            data.append(jsonArray[0]['contents']['contents'][0])

    jsonArray[0]['contents']['contents'] = data

    return jsonArray


def combine_flex_carousel_json(template_jsonfile, reply_jsonfile,date_tour):
    with open(template_jsonfile, encoding='utf8') as f:
        templateArray = json.load(f)
    
    columns = setup_tour_card(reply_jsonfile, date_tour)
    tour_card = []
    tour_card.append(columns)
    templateArray[0]['contents']['contents'] = tour_card
    
    return templateArray

def setup_tour_card(reply_jsonfile,date_tour):
    
    with open(reply_jsonfile, encoding='utf8') as f:
        jsonArray = json.load(f)
    
    title = jsonArray[0]['title']
    res = requests.get(jsonArray[0]['actions'][1]['uri'],
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36",
        })

    html = BeautifulSoup(res.text,'html.parser')

    tourA = html.find('article',class_="tourArticle")
    n = 1
    journey = {}
    while tourA.find('div',class_="tourline"+str(n)):
        tourline = tourA.find('div',class_="tourline"+str(n))
        line = tourA.find('div',class_="tourline")
        line = [h.text.strip() for h in line.find_all('h5')]
        journey[tourline.find('h4').text]= line
        # journey[tourline.find_all('h4')[0].text] = journey[tourline.find_all('h4')[0].text] + tourline.find_all('h5')
        n += 1

    tour = []   
    for d in range(len(journey)): # 看有幾天的行程

      day=[{
      "type": "text",
      "text": "第一天",
      "size": "md"
      },
      {
        "type": "box",
        "layout": "vertical",
        "contents": [],
        "height": "5px"
      }]
    
      day[0]['text'] = "第"+ str(d+1)+"天"
      tour.append(day[0])
      tour.append(day[1])
      for s in journey["第"+ str(d+1)+"天"]: # 看看有幾個景點
          Attractions={
          "type": "box",
          "layout": "horizontal",
         "contents": [
          {
            "type": "box",
            "layout": "vertical",
            "contents": [
              {
                "type": "filler"
              },
              {
                "type": "box",
                "layout": "vertical",
                "contents": [],
                "cornerRadius": "30px",
                "height": "12px",
                "width": "12px",
                "borderColor": "#6486E3",
                "borderWidth": "2px"
              },
              {
                "type": "filler"
              }
            ],
            "flex": 0
          },
          {
            "type": "text",
            "text": "Akihabara",
            "gravity": "center",
            "flex": 4,
            "size": "sm"
          }
          ],
          "spacing": "md",
          "cornerRadius": "30px"
          }
          Att_connection={
             "type": "box",
             "layout": "horizontal",
             "contents": [
             {
              "type": "box",
              "layout": "vertical",
              "contents": [
                {
                  "type": "box",
                  "layout": "horizontal",
                  "contents": [
                    {
                      "type": "filler"
                    },
                    {
                      "type": "box",
                      "layout": "vertical",
                      "contents": [],
                      "width": "2px",
                      "backgroundColor": "#6486E3"
                    },
                    {
                      "type": "filler"
                    }
                  ],
                  "flex": 1
                }
              ],
              "width": "12px"
              }
            ],
            "spacing": "md",
            "height": "20px"
          }
          Attractions['contents'][1]['text'] = s # 修改景點的名字
          tour.append(Attractions)
          tour.append(Att_connection)

    with open('img/tour_card_template.json', encoding='utf8') as f:
        templateArray = json.load(f)
    
    templateArray['body']['contents'] = tour[:-1:]
    templateArray['header']['contents'][0]['contents'][0]['text'] = date_tour # 出發時間
    templateArray['header']['contents'][0]['contents'][1]['text'] = title # 標題
    templateArray['footer']['contents'][0]['contents'][0]['action']['uri'] = jsonArray[0]['actions'][1]['uri'] # 詳細內容

    return templateArray
   