import requests 
from bs4 import BeautifulSoup
import json
import codecs

# travel type
# url = "https://www.taiwan.net.tw/m1.aspx?sNo=0000108" # travel type
# res = requests.get(url,
# headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36",
# "Referer": "https://www.taiwan.net.tw/m1.aspx?sNo=0001037"
# })

# html = BeautifulSoup(res.text,'html.parser')
# data = html.find('ul',class_= "grid lattice-list")
# website = "https://www.taiwan.net.tw/"

# data_array = []
# for d in data.find_all('a'):
#     object_dict = {}
#     object_dict["type"] = "postback" 
#     object_dict["data"] = f"{website}{d['href']}"
#     object_dict["ImageUrl"] = d.find('img',class_='lazyload')['data-src']
#     object_dict["text"] = d.find("img",class_="lazyload")["alt"]
#     print(object_dict["text"])
#     json_object = json.dumps(object_dict, indent = 4)
#     data_array.append(json_object)



ip_pair={"00120":"樂齡親子","24438":"原鄉","01033":"美食","01034":"文化","01035":"溫泉",
"01036":"樂活","01037":"離島","01038":"生態","01039":"鐵道","01040":"夜市"}

for ip in ip_pair.keys():
    url1 = "https://www.taiwan.net.tw/m1.aspx?sNo=00"+ ip
    res = requests.get(url1,
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36",
    "Referer": "https://www.taiwan.net.tw/m1.aspx?sNo=0000108"
    })

    html = BeautifulSoup(res.text,'html.parser')
    data = html.find('ul',class_= "grid card-list card-style-columns")
    website = "https://www.taiwan.net.tw/"
    data = data.find_all('li')

    data_array = []
    count = 0
    for d in data:
        count += 1
        object_dict = {}
        object_dict["title"] = d.find('a',class_="card-link")['title']
        object_dict["actions"] = [{
                        "type": "datetimepicker",
                        "Label": "選擇預定出發日期",
                        "mode": "date",
                        "data": "date",
                        "initial": "2021-10-30",
                        "min": "2021-10-20",
                        "max": "2021-11-20"
                      },{
                    "type": "uri",
                    "label": "詳細內容",
                    "text": "詳細內容",
                    "uri": website + d.find('a',class_="card-link")['href']
                }]
        url = website+d.find('a',class_="card-link")['href']
        res = requests.get(url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36",
        "Referer": url1
        })

        html = BeautifulSoup(res.text,'html.parser')
        tourA = html.find('article',class_="tourArticle")
        object_dict["thumbnailImageUrl"] = website + tourA.find('img')['src'].replace('https://www.taiwan.net.tw/','')
        n = 1
        journey = {}
        while tourA.find('div',class_="tourline"+str(n)):
            tourline = tourA.find('div',class_="tourline"+str(n))
            line = tourA.find('div',class_="tourline")
            line = [h.text.strip() for h in line.find_all('h5')]
            journey[tourline.find('h4').text]= tourline.find('h4').text + '-'.join(line)
            # journey[tourline.find_all('h4')[0].text] = journey[tourline.find_all('h4')[0].text] + tourline.find_all('h5')
            n += 1

        object_dict["text"] = ''
        for i in range(len(journey)):
            if i == 0:
                if len(journey["第"+ str(i+1)+"天"])<30 or (len(journey["第"+ str(i+1)+"天"])<60 and len(journey)==1):
                    object_dict["text"] = object_dict["text"] + journey["第"+ str(i+1)+"天"]
                else:
                    a = journey["第"+ str(i+1)+"天"].strip().replace(' ','')
                    object_dict["text"] = object_dict["text"] + a[:a.find('-')]+'-'+a[len(a)-a[::-1].find('-')::]
            else:
                if len(journey["第"+ str(i+1)+"天"])<30:
                    object_dict["text"] = object_dict["text"] +';' + journey["第"+ str(i+1)+"天"]
                else:
                    a = journey["第"+ str(i+1)+"天"].strip().replace(' ','')
                    object_dict["text"] = object_dict["text"] +';' + a[:a.find('-')]+'-'+a[len(a)-a[::-1].find('-')::]
        if len(object_dict["text"])>60:
            object_dict["text"] = object_dict["text"][0:60]
        
        object_dict["data"] = "folder=website&tag="+ip_pair[url1[-5:]]+"&label="+str(count)

    #     print(object_dict["text"])
        json_object = json.dumps(object_dict, ensure_ascii=False, indent=4)
        data_array.append(json_object)

    with codecs.open(ip_pair[url1[-5:]]+'_website.json', 'w',encoding='utf-8') as f:
        content = ', '.join(data_array)
        content = '[' + content + ']'
        f.write(content)
