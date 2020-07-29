# -*- coding: utf-8 -*-
# Copied from chat_0.60py
# Add word2vec on 2019/09/04
'''
See: https://github.com/line/line-bot-sdk-python/issues/37
When you press the verify button, LINE Server send a webhook.
But it is dummy.
Your server receive webhook and try to call Reply API.
But reply token is also dummy, so it failed...
'''

from __future__ import unicode_literals

import os, sys, re, random, sqlite3, time
# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', '')
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')

from argparse import ArgumentParser
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    TemplateSendMessage, ConfirmTemplate, MessageAction,
    ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URIAction,
    PostbackAction, DatetimePickerAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage, FileMessage,
    FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent,
    TextComponent, SpacerComponent, IconComponent, ButtonComponent,
    SeparatorComponent, QuickReply, QuickReplyButton,
    ImageSendMessage
)

from linebot.models.sources import (
    SourceUser, SourceGroup, SourceRoom,
)

import Chat_DB
chatDB = Chat_DB.Chat_DB()
import joke_db
#(sim_threshold, DocFile) = (sys.argv[1], sys.argv[2])
(sim_threshold, DocFile) = (0.3, 'Chat_DB.db')
sim_threshold = float(sim_threshold) 
print(len(sys.argv), sim_threshold, DocFile)
jdb = joke_db.joke_db(InFile=DocFile)
jdb.SetTexts()
jdb.MakeIndex()
app = Flask(__name__)

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)
line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)


def processCommand(channelID, userID, txt):
    """Given an input string with the format:
    Command：:Question：:Answer
    insert the dialogue into the database Table: TinMsg.
    Note: the colon can be either in Chinese or in ASCII code
    Command include:
    紀錄: insert Question and Answer into the chat database
    刪除: delete Question and Answer pair from the database
    return "Command done!" or return None if not command
    """
    msgL = re.split(r'[:：]\s*[:：]', txt, 2)
    # see: https://stackoverflow.com/questions/12871066/what-exactly-is-a-raw-string-regex-and-how-can-you-use-it
    if len(msgL) != 3: # if not "紀錄：：問句：：回話"
        return None
    cmd = msgL.pop(0)
#    print(str(msgL))
    if cmd == '紀錄' or cmd == '愛貓學說話' or cmd != "":
        chatDB.insert('TqaBase', channelID, userID, msgL[0], msgL[1])
    elif cmd == '刪除':
        chatDB.delete('TqaBase', channelID, userID, msgL[0], msgL[1])
    else:
        return "命令格式：[紀錄|刪除]::問話::回應"
    return cmd + " done (完成)!"

data = {}
getorder = {}
grouporder = {}
scoreorder = {}
intxt = {}
joke = {}


def getAnswer(chID, uID, txt, event):
    """Given a user text, return a response text"""
#    dic = {'嗨':'你好！', '再見':'祝你有美好的一天', '1':'安靜嗎？'}
#    return dic[txt] if txt in dic else txt
    if txt[0:5] == '小明小明，':
        received_text = txt[5:].split('，')
        app.logger.warning("\nreceived_text: " + received_text[0])
        data[uID] = received_text[0]
        #outL = chatDB.select('TqaBase', channelID=chID, userID=uID, inmsg=data[uID])
        outL = None
        print("outL=", outL)
        if outL is None:
            # search QA data for response
            SimTexts = jdb.GetSimilarText(data[uID], sim_threshold)
            if len(SimTexts) == 0: # no similar text
                ans = '沒有該關鍵字的笑話ˊˋ'
                return ans # echo what the user type
            else:
                conn = sqlite3.connect('Chat_DB.db')
                cur = conn.cursor()
                cur.execute("SELECT inmsg FROM TioMsg WHERE channelID =? AND inmsg =? AND userID =?", (chID, txt, uID))
                W = cur.fetchall()
                app.logger.warning("\ngetanswerfun:"+str(W))
                if len(W) == 0:
                    getorder[uID] = 0
                else:
                    try:
                        getorder[uID]
                    except KeyError:
                        getorder[uID] = len(W)
                try:
                    ans = SimTexts[getorder[uID]][2] # return most similar one
                    getorder[uID] = getorder[uID]+1
                except IndexError:
                    ans = '沒有該關鍵字的笑話了_(┐「ε:)_'
        elif len(outL) == 1: 
            outL = outL[0]
            ans = outL[3]
        else:
            outL = selectAnswer(chID, uID, outL)
            ans = outL[3]
        return ans

    elif '小明小明' not in txt[0:3]:
        received_text = txt
        data[uID] = str(received_text)
        #outL = chatDB.select('TqaBase', channelID=chID, userID=uID, inmsg=data[uID])
        outL = None
        print("outL=", outL)
        intxt[uID] = 'None'
        if outL is None:
            # search QA data for response
            SimTexts = jdb.GetSimilarText(data[uID], sim_threshold)
            if len(SimTexts) == 0: # no similar text
                return data[uID] # echo what the user type
            else:
                conn = sqlite3.connect('Chat_DB.db')
                cur = conn.cursor()
                cur.execute("SELECT inmsg FROM TioMsg WHERE channelID =? AND inmsg =? AND userID =?", (chID, txt, uID))
                W = cur.fetchall()
                app.logger.warning("\ngroupanswerfun:"+str(W))
                if len(W) == 0:
                    grouporder[uID] = 0
                else:
                    try:
                        grouporder[uID]
                    except KeyError:
                        grouporder[uID] = len(W)
                
                #grouporder[uID] = len(W)
                try:
                    ans = SimTexts[grouporder[uID]][2] # return most next one
                    grouporder[uID] = grouporder[uID]+1
                except IndexError:
                    ans = '沒有該關鍵字的笑話了┐(´д`)┌'
        elif len(outL) == 1: 
            outL = outL[0]
            ans = outL[3]
        else:
            outL = selectAnswer(chID, uID, outL)
            ans = outL[3]
        return ans

def feedback(event):
    bubble = BubbleContainer(direction='ltr',
    body=BoxComponent(layout='vertical',
        contents=[
                # title
                TextComponent(text='笑話回饋', weight='bold', size='xl'),
                # info
                BoxComponent(layout='vertical', margin='lg', spacing='sm',
                    contents=[
                        BoxComponent(layout='baseline', spacing='sm',
                            contents=[
                                TextComponent(
                                    text='請問您覺得這個笑話好笑嗎?',
                                    color='#aaaaaa',
                                    size='sm',
                                    flex=1
                                ),
                            ],
                        )
                    ],
                    )
        ],),
    footer=BoxComponent(layout='vertical', spacing='sm',
        contents=[
            # callAction
            ButtonComponent(
                style='link',
                height='sm',
                action=MessageAction(label='好笑', text= '好笑'),
            ),
            ButtonComponent(
                style='link',
                height='sm',
                action=MessageAction(label='有點好笑', text= '有點好笑'),
            ),
            ButtonComponent(
                style='link',
                height='sm',
                action=MessageAction(label='不好笑', text= '不好笑'),
            ),

        ]
    ),
    )
    message = FlexSendMessage(alt_text="笑話回饋", contents=bubble)
    return message

def more(txt, event, userID):
    bubble  = BubbleContainer(direction='ltr',
    body=BoxComponent(layout='vertical',
        contents=[
                # title
                TextComponent(text='是否再來一個笑話?', weight='bold', size='xl'),
                # info
                BoxComponent(layout='vertical', margin='lg', spacing='sm',
                    contents=[
                        BoxComponent(layout='baseline', spacing='sm',
                            contents=[
                                TextComponent(
                                    text='是否再來一個相同關鍵字的笑話?',
                                    color='#aaaaaa',
                                    size='sm',
                                    flex=1
                                ),
                            ],
                        )
                    ],
                    )
        ],),
    footer=BoxComponent(layout='vertical', spacing='sm',
        contents=[
            # callAction
            ButtonComponent(
                style='link',
                height='sm',
                action=MessageAction(label='再來一個', text= intxt[userID]),
            ),
            ButtonComponent(
                style='link',
                height='sm',
                action=MessageAction(label='不用', text= '不用'),
            ),
        ]
    ),
    )
    message = FlexSendMessage(alt_text="再來一個", contents=bubble)
    return message 

def ask(txt, event):
    bubble  = BubbleContainer(direction='ltr',
    body=BoxComponent(layout='vertical',
        contents=[
                # title
                TextComponent(text='是否有達到破冰效果?', weight='bold', size='xl'),
                # info
                BoxComponent(layout='vertical', margin='lg', spacing='sm',
                    contents=[
                        BoxComponent(layout='baseline', spacing='sm',
                            contents=[
                                TextComponent(
                                    text='在特定場合使用是否有達到破冰效果呢?',
                                    color='#aaaaaa',
                                    size='sm',
                                    flex=1
                                ),
                            ],
                        )
                    ],
                    )
        ],),
    footer=BoxComponent(layout='vertical', spacing='sm',
        contents=[
            # callAction
            ButtonComponent(
                style='link',
                height='sm',
                action=MessageAction(label='有', text= '有達到破冰效果'),
            ),
            ButtonComponent(
                style='link',
                height='sm',
                action=MessageAction(label='沒有', text= '沒有達到破冰效果'),
            ),
        ]
    ),
    )
    message = FlexSendMessage(alt_text="是否破冰", contents=bubble)
    return message   


def selectAnswer(chID, uID, ansL): 
    """Given multiple (query, reply) tuples in a list, 
    return a reply in a tuple that has not yet been used for the given query.
    If all replies have been used, just return a random tuple."""
    for t in ansL: # for each tulple in the list
        L = chatDB.select('TioMsg', channelID=chID, userID=uID, inmsg=t[2], reply=t[3])
        if L is None: return t
    return random.choice(ansL)

def setReply(channelID, userID, inputMsg, replyMsg):
#    profile = line_bot_api.get_profile(event.source.user_id)
    profile = line_bot_api.get_profile(userID)
    chatDB.insertTioMsg(channelID, userID, inputMsg, replyMsg, profile.display_name)

def setScore(channelID, userID, inputMsg, txt, event):
    profile = line_bot_api.get_profile(userID)
    chatDB.insertscore(channelID, userID, inputMsg, txt, profile.display_name)

def breakice(channelID, userID, inputMsg, txt, event):
    profile = line_bot_api.get_profile(userID)
    chatDB.insertbreakice(channelID, userID, inputMsg, txt, profile.display_name)

def mode(channelID, userID, inputMsg, txt, event):
    profile = line_bot_api.get_profile(userID)
    chatDB.insertmode(channelID, userID, inputMsg, txt, profile.display_name)


def randomAnswer(chID, uID, txt, event):
    conn = sqlite3.connect('Chat_DB.db')
    cur = conn.cursor()
    sql = "SELECT txt FROM TjokeBase WHERE jokeScore = '5' OR jokeScore = '4' OR jokeScore = '3'"
    cur.execute(sql)
    outL = cur.fetchall()
    app.logger.warning("隨機模式")
    return random.choice(outL)
    

    

# Use globals: request, app, parser
def getEvents():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True) # body is a text string
    app.logger.warning("\nRequest body: " + body)
    try: events = parser.parse(body, signature)
    except InvalidSignatureError: abort(400)
    return events

# Use globals: MessageEvent, TextMessage
def getID(event):
    """Given a event, to know which room, group, or single user
    the sender is.
    The sender could be in a room (with a value in room_id),
    or a group (with a value in group_id). However, if the sender
    is by him/her-self, these two attributes would have no value.
    The sender would have a value in user_id if both room_id and
    group_id have no value.
    The sender may not have a value in user_id if the sender is
    from a room or from a group.
    """
    (chID, userID) = (None, None)
    if isinstance(event.source, SourceRoom):
#        profile = line_bot_api.get_room_member_profile(event.source.room_id, event.source.user_id)
        chID = event.source.room_id
    elif isinstance(event.source, SourceUser):
#        profile = line_bot_api.get_profile(event.source.user_id)
        chID = event.source.user_id
        userID = event.source.user_id
    elif isinstance(event.source, SourceGroup):
#        profile = line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id)
        chID = event.source.group_id
        userID = event.source.user_id
#    if chID:
    #        app.logger.warning("name: " + profile.display_name)
    #        app.logger.warning("user_id: " + profile.user_id)
    #        app.logger.warning("pic_url: " + profile.picture_url)
    #        app.logger.warning("status: " + str(profile.status_message))
#        return chID
    return (chID, userID)

def handleNonMessageEvent(event):
    if event.source.user_id:
        profile = line_bot_api.get_profile(event.source.user_id)
        msg_list = [TextSendMessage(text="Hi!"+profile.display_name + "\n歡迎加入破冰機器人-小明同學官方帳號(ゝ∀･)")]
        msg_list.append(TextSendMessage(text="輸入「小明小明，關鍵字」即可搜尋關鍵字笑話\n輸入「小明功能」可查看小明同學的操作說明"))
        msg_list.append(TextSendMessage(text="有任何建議都歡迎填寫表單回饋喔♥(´∀` )人\nhttps://docs.google.com/forms/d/e/1FAIpQLSf3btrWypa9L43CIfF6VpK6bSwegU3pfS3pv6L2tkltZ7BoCw/viewform"))
    else:
        msg_list = []
    if event.type == 'join':
        msg_list = [TextSendMessage(text="Hi!\n感謝您邀請小明(,,・ω・,,)")]
        msg_list.append(TextSendMessage(text="輸入「小明小明，關鍵字」即可搜尋關鍵字笑話\n輸入「小明功能」可查看聊天小明同學的操作說明"))
    elif event.type == 'leave':
        if isinstance(event.source, SourceGroup):
            line_bot_api.reply_message(
                event.reply_token, TextMessage(text='我離開了。再見！'))
            line_bot_api.leave_group(event.source.group_id)
        elif isinstance(event.source, SourceRoom):
            line_bot_api.reply_message(
                event.reply_token, TextMessage(text='我離開了。再見！'))
            line_bot_api.leave_room(event.source.room_id)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(text="Bot can't leave from 1:1 chat"))

    else:
        #msg_list.append(TextSendMessage(text=event.type))
        pass

    line_bot_api.reply_message( # reply to Line and then to the user
        event.reply_token,
        msg_list
    )
    
# Use globals: line_bot_api, TextSendMessage
@app.route("/", methods=['POST'])
def callback():
    events = getEvents() # get events from Line triggered by the user
    for event in events: # normally only one event in events
        (channelID, userID) = getID(event)
        if not isinstance(event, MessageEvent):
            handleNonMessageEvent(event)
            continue
        print("channelID=", channelID, "userID=", userID)
        inputMsg = event.message.text if isinstance(event.message, TextMessage) else ""
        print("inputMsg='"+inputMsg+"'")
        replyMsg = processCommand(channelID, userID, inputMsg)
        print("replyMsg='"+str(replyMsg)+"'")
        msg_list = []

        if inputMsg == '小明功能':
            replyMsg = "輸入「小明小明，關鍵字」即可搜尋關鍵字笑話\n例如:輸入「小明小明，圖書」即可搜尋有關「圖書」的笑話٩(๑•̀ω•́๑)۶"
            msg_list.append(TextSendMessage(text=replyMsg))
        
        if inputMsg =='小明推薦':
            image_message = ImageSendMessage(original_content_url='https://images.plurk.com/5oJ4NdzsaWNSOrJtHRnBxU.jpg',preview_image_url='https://images.plurk.com/5v9ox6h9aLVRfDsybRpUjH.jpg')
            app.logger.warning("picture get!")
            msg_list.append(image_message)
            line_bot_api.reply_message( # reply to Line and then to the user
            event.reply_token,
            msg_list
            )
            continue

        #try:
        if inputMsg =='小明隨機':
            intxt[userID] = inputMsg
            outL= randomAnswer(channelID, userID, inputMsg, event)
            replyMsg = outL[0]
            mode(channelID, userID, inputMsg, replyMsg, event)
            conn = sqlite3.connect('Chat_DB.db')
            cur = conn.cursor()
            cur.execute("SELECT title FROM TjokeBase WHERE txt = ?", (replyMsg,))
            T = cur.fetchall()
            if len(T)>0:
                for index in range(len(T)):
                    title = '標題:'+T[index][0]
                msg_list.append(TextSendMessage(text=title))
            msg_list.append(TextSendMessage(text=replyMsg))
            joke[userID] = replyMsg
            message = feedback(event)
            msg_list.append(message)

        elif '好笑' in inputMsg:
            setScore(channelID, userID, inputMsg, joke[userID], event)
            bubble1 = ask(inputMsg, event)  
            msg_list.append(bubble1)
        
        elif '達到破冰效果' in inputMsg:
            breakice(channelID, userID, inputMsg, joke[userID], event)
            bubble2 = more(inputMsg, event, userID) 
            msg_list.append(bubble2)

        elif inputMsg == '不用':
            replyMsg = '收到(๑•̀ㅂ•́)و✧'
            msg_list.append(TextSendMessage(text=replyMsg))
        
        elif inputMsg == 'None':
            replyMsg = '麻煩再重新輸入一次關鍵字<(_ _)>'
            msg_list.append(TextSendMessage(text=replyMsg))

        elif replyMsg is None: # if not "紀錄：：問句：：回話"
            if inputMsg[0:5] == '小明小明，':
                intxt[userID] = inputMsg
            replyMsg = getAnswer(channelID, userID, inputMsg, event)
            mode(channelID, userID, inputMsg, replyMsg, event)
            try:
                if replyMsg == data[userID]:
                    continue
            except BaseException:
                    pass
            conn = sqlite3.connect('Chat_DB.db')
            cur = conn.cursor()
            cur.execute("SELECT title FROM TjokeBase WHERE txt = ?", (replyMsg,))
            T = cur.fetchall()
            if len(T)>0:
                for index in range(len(T)):
                    title = '標題:'+T[index][0]
                msg_list.append(TextSendMessage(text=title))

            msg_list.append(TextSendMessage(text=replyMsg))
            joke[userID] = replyMsg
            if '沒有該關鍵字的笑話' not in replyMsg and '麻煩再重新輸入一次關鍵字<(_ _)>' not in replyMsg:
                message = feedback(event)
                msg_list.append(message)
        '''
        except BaseException:
            replyMsg = '請按照規則詢問喔(つд⊂)'
            msg_list.append(TextSendMessage(text=replyMsg))
        '''
        print("Aftr getAnswer:"+str(replyMsg))
        print("After setReply: ...")
        line_bot_api.reply_message( # reply to Line and then to the user
        event.reply_token,
        msg_list
        )
    setReply(channelID, userID, inputMsg, replyMsg)
    return 'OK' # response 200


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    handler = RotatingFileHandler('chat.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    app.run(debug=options.debug, port=options.port)
'''
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    arg_parser.add_argument('-s', '--surrogate', default=False, help='False means no ngrok')
    options = arg_parser.parse_args()

    handler = RotatingFileHandler('chat.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    if options.surrogate: # $ python chat_0.14 -s
        app.run(debug=options.debug, port=options.port)
    else: # $ sudo python chat_0.14.py
        context = (
            '/etc/letsencrypt/live/bot.glis.ntnu.edu.tw/fullchain.pem',
            '/etc/letsencrypt/live/bot.glis.ntnu.edu.tw/privkey.pem')
        app.run(debug=options.debug, port=options.port, host="0.0.0.0", ssl_context=context)
'''
