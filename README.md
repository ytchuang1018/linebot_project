## LineBot Project
[網頁版說明](https://ytchuang1018.github.io/linebot_project/)

在疫情解封後, 大家對於國旅有相當大的興趣, 但建立行程會花很多時間, 

因此, 這個機器人可以協助用戶快速建立行旅程, 並解決分攤旅費問題

### Demo
[Demo影片](https://tinyurl.com/yfpke2ak)

### 加入好友
就i趴趴GO 
@008xyyhr

[就i趴趴GO](https://liff.line.me/1645278921-kWRPP32q/?accountId=008xyyhr)

### 建立流程
主要以python3撰寫程式, 整個程式在GCP部署, 在heroku部署旅費分攤的html

1. 資料準備: 爬到台灣交通部觀光局上的推薦行程, 可以用分類行程來快速找到旅行目的

2. linebot設計: 
   * 圖文選單: 提供主功能選單讓大家可以快速找到功能
   * 影像地圖: 把先前網路上爬到的推薦行程的分類以影像地圖呈現, 可以直接點選
   * flex訊息: 加入喜歡的行程後, 進入日期選擇, 作成旅行小卡
   * 多頁訊息: 用戶輸入關鍵字或是點選按鈕, 機器人就會自動回覆
   * LIFF應用: 連接旅費分攤的網頁
   * 歷史旅程: 可以看到已完成的行程小卡
   * 查詢旅程: 可以看到進行中的行程小卡
   * 刪除行程: 可以刪除進行中的行程小卡，己完成的就設定無法刪除

3. 旅費分攤的網頁: 用html寫出網頁, 利用javascript可以讓用戶可以新增旅伴及費用項目, 幫忙計算出旅費的分攤, 再部署到heroku
   heroku login->heroku git:remote -a project/git remote add heroku git@heroku.com:project.git -> git push heroku master

4. GCP服務: 
   * google shell: 撰寫程式
   * google cloud storage: 爬蟲資料, 給用戶看到的行程, 及當用戶加入行程或完成行程就處理原先在storage中的小卡
   * google cloud firestore: 存用戶資料
   * google cloud run: 部署linebot

### 待完成
1. 加入自由行: 更彈性的調整行程
2. 加入跟團: 讓老人家可以更快找到跟團行程
