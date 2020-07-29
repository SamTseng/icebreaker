# 破冰機器人


## 1. Introduction
「小明同學」中文破冰機器人

## 2. Files

**word2vec**: Put your word2vec object in this folder

**Chat_DB.py** :資料庫創建和存取

**chat_personal.py** : LINE機器人主程式(個人聊天室)

**joke_db.py** : 建立索引和查詢

**jokeExcel2DB.py** : 將excel資料匯入資料庫

**richmenu.ipynb** : 建立圖文選單



## 3.Runserver
* create Chat_DB.db
```
Chat_DB.py
```

* insert jokes to database
```
python jokeExcel2DB.py filename.xlsx
```

* run chatbot
```
python chat_personal.py
```


## 4.TBP
**chat_0.60.py**: LINE機器人主程式(群組)
```
小明狀態:查詢chatbot活動狀態
小明安靜:chatbot停止回覆
小明說話:chatbot開始回覆
```

## 5.Changelog
*2019.12.11
  * +mode field
*2019.12.11
  * icebreak field
*2019.11.13
  * +小明推薦
  * +小明隨機
*2019.09.16
  * *Fix index problem
*2019.09.12
  * *Change Template messages to Flex Message
  * +richmenu.ipynb
*2019.09.06
  * +word2vec
* 2019.07.21
  * +jokeExcel2DB.py