#/usr/bin/env python
# -*- coding: utf-8 -*-
# Written by Sam Tseng on 2018/01/31, last modified on 2018/04/19
# Currently SQLite3 is used
# To use MySQL, see: https://blog.gtwang.org/programming/python-mysqldb-connect-mysql-database-tutorial/

import sqlite3
import sys, time, re
from datetime import datetime

class Chat_DB():
    '''
    Given a file containing multiple documents in CSV format,
    return a document each time nextdoc() is called.
    So far this class is only for the download CSV format from CCR
    '''
    def __init__(self, InFile='Chat_DB.db', DBis='SQLite'):
        self.dbFile = InFile
        self.DBis = DBis
        if DBis == 'SQLite':
            self.conn = sqlite3.connect(InFile, check_same_thread=False)
        else:
            sys.stderr.write('Please specify a database, like SQLite, MySQL, ...')
        cur = self.conn.cursor()
#        cur.execute('DROP TABLE TioMsg')
# TioMsg:所有對話的紀錄資料表
        cur.execute("""CREATE TABLE IF NOT EXISTS TioMsg (
            channelID text,
            userID text,
            userName text,
            inmsg text,
            reply text,
            logtime text,
            datetime text
            )""")
# TqaBase:問答資料表：可由使用者教導chatbot如何回應問題
        cur.execute("""CREATE TABLE IF NOT EXISTS TqaBase (
            channelID text,
            userID text,
            inmsg text,
            reply text,
            logtime text
            )""")
# TjokeBase:笑話語料，供查詢使用
        cur.execute("""CREATE TABLE IF NOT EXISTS TjokeBase (
            "jokeID"	text,
            "title" text,
            "txt"	text,
            "category" text,
            "jokeScore"	text
            )""")
# Tscore:使用者回饋的笑話好笑程度資料表
        cur.execute("""CREATE TABLE IF NOT EXISTS Tscore (
            "userID"	text,
            "userName"	text,
            "jokeID"	text,
            "score"	text,
            "breakice" text,
            "mode" text,
            "logtime"	text,
            "datetime"	text
            )""")

    def __del__(self):
        self.conn.close()

    def insertTioMsg(self, channelID, userID, inmsg, reply, userName):
        """Record the input/output message in this table.
        Record which user in which channel interact with the chatbot"""
        cur = self.conn.cursor()
        logtime = time.time()
        dt_object = datetime.fromtimestamp(logtime)
        if channelID == None:  channelID = 1
        cur.execute("INSERT INTO " + "TioMsg" +
        " (channelID, userID, userName, inmsg, reply, logtime, datetime) VALUES (?, ?, ?, ?, ?, ?, ?)"
        , (channelID, userID, userName, inmsg, reply, logtime, str(dt_object)))
        self.conn.commit()
    
    def insertmode(self, channelID, userID, inputMsg, txt, userName):
        cur = self.conn.cursor()
        cur.execute("SELECT jokeID FROM TjokeBase WHERE txt =?", (txt,))
        ID = cur.fetchall()
        pattern = '[A-Za-z0-9_]+'
        ansID = re.findall(pattern,str(ID))
        print(ansID)
        logtime = time.time()
        dt_object = datetime.fromtimestamp(logtime)
        if inputMsg == '小明隨機':
            cur.execute("INSERT INTO Tscore (userID, userName, jokeID, mode, logtime, datetime) VALUES (?,?,?,?,?,?)"
            ,(userID, userName, str(ansID[0]), str('隨機'), logtime, str(dt_object)))
        else:
            cur.execute("INSERT INTO Tscore (userID, userName, jokeID, mode, logtime, datetime) VALUES (?,?,?,?,?,?)"
            ,(userID, userName, str(ansID[0]), str('查詢'), logtime, str(dt_object)))
        self.conn.commit()
    
    def insertscore(self, channelID, userID, inputMsg, txt, userName):
        cur = self.conn.cursor()
        cur.execute("SELECT jokeID FROM TjokeBase WHERE txt =?", (txt,))
        ID = cur.fetchall()
        pattern = '[A-Za-z0-9_]+'
        ansID = re.findall(pattern,str(ID))
        print(ansID)
        if inputMsg == '好笑':
            sql = "UPDATE Tscore SET score = ?  WHERE userID = ? AND jokeID = ?"
            val = ('5', userID, str(ansID[0]))
            cur.execute(sql, val)
        if inputMsg == '有點好笑':
            sql = "UPDATE Tscore SET score = ? WHERE userID = ? AND jokeID = ?"
            val = ('3', userID, str(ansID[0]))
            cur.execute(sql, val)
        if inputMsg == '不好笑':
            sql = "UPDATE Tscore SET score = ? WHERE userID = ? AND jokeID = ?"
            val = ('0', userID, str(ansID[0]))
            cur.execute(sql, val)
        self.conn.commit()
    
    def insertbreakice(self, channelID, userID, inputMsg, txt, userName):
        cur = self.conn.cursor()
        cur.execute("SELECT jokeID FROM TjokeBase WHERE txt =?", (txt,))
        ID = cur.fetchall()
        pattern = '[A-Za-z0-9_]+'
        ansID = re.findall(pattern,str(ID))
        sql = "UPDATE Tscore SET breakice = ?  WHERE userID = ? AND jokeID = ?"
        val = (inputMsg, userID, str(ansID[0]))
        cur.execute(sql, val)
        #print( "breakice:" + inputMsg + "userID:" + userID + "jokeID:" +str(ansID[0]))
        self.conn.commit()

    def insert(self, Table, channelID, userID, inmsg, reply):
        """Record the taught dialogue or input/output message in this table.
        Record which user in which channel teach the chatbot for dialogue"""
        cur = self.conn.cursor()
        logtime = time.time()
        if channelID == None:  channelID = 1
        cur.execute("INSERT INTO " + Table +
        " (channelID, userID, inmsg, reply, logtime) VALUES (?, ?, ?, ?, ?)"
        , (channelID, userID, inmsg, reply, logtime))
        self.conn.commit()

    def delete(self, Table, channelID='%', userID='%', inmsg='%', reply='%'):
#    def delete(self, *msgL):
#        (channelID, inmsg, reply) = map(lambda x: x if x else '%', msgL)
        cur = self.conn.cursor()
        cur.execute("DELETE FROM " + Table + """ WHERE
        channelID like ? userID like ? AND inmsg like ? AND reply like ? """
        , (channelID, userID, inmsg, reply))
        self.conn.commit()

#    def random(self, Table, channelID='%', userID='%', inmsg='%', reply='%'):
#        cur = self.conn.cursor()
#        sql = "SELECT txt FROM TjokeBase WHERE jokeScore = '3' OR jokeScore = '4' OR jokeScore = '5'"
#        cur.execute(sql)


    def select(self, Table, channelID='%', userID='%', inmsg='%', reply='%'):
#    def selectTioMsg(self, msgL):
#        (channelID, inmsg, reply, logtime) = map(lambda x: x if x else '%', msgList)
        cur = self.conn.cursor()
        if channelID == None: channelID = '%'
        cur.execute("SELECT channelID, userID, inmsg, reply, logtime FROM "
        + Table + " WHERE channelID like ? AND userID like ? AND inmsg like ? "
        + " And reply like ?", [channelID, userID, inmsg, reply])
        outL = cur.fetchall()
#        print("1. ", channelID, userID, inmsg, "\n", outL)
        if len(outL) > 0: return outL
            # return latest recorded dialogue
#            return sorted(outL, key=lambda x:-float(x[-1]))[0]
#            return outL[-1] # the last record is the latest, same as the above

        # if no dialogue in a channel by a user, look for a reply in the channel
        cur.execute("SELECT channelID, userID, inmsg, reply, logtime FROM "
        + Table + " WHERE channelID like ? AND inmsg like ? "
        , [channelID, inmsg])
        outL = cur.fetchall()
#        print("2. ", channelID, userID, inmsg, "\n", outL)
        if len(outL)>0: return outL
#            return sorted(outL, key=lambda x:-float(x[-1]))[0]
#            return outL[-1] # the last record is the latest, same as the above

        # if no dialogue in any channel by any user, look for a reply in any channel
        cur.execute("SELECT channelID, userID, inmsg, reply, logtime FROM "
#        + Table + " WHERE inmsg like ? ", (inmsg)) # this line causes an error
        + Table + " WHERE inmsg like ? ", [inmsg])
# see: https://stackoverflow.com/questions/16856647/sqlite3-programmingerror-incorrect-number-of-bindings-supplied-the-current-sta
        outL = cur.fetchall()
#        print("3. ", channelID, userID, inmsg, "\n", outL)
        if len(outL)>0: return outL
#            return sorted(outL, key=lambda x:x[3])[-1]
        else: return None


if __name__ == "__main__":
#    chatDB = Chat_DB(InFile='Test.db')
    chatDB = Chat_DB(InFile='Chat_DB.db')

'''
#   chatDB.delete('TqaBase')
    chatDB.insert('TqaBase', 1, 1, '嗨', '你好')
    time.sleep(0.1)
    chatDB.insert('TqaBase', 1, 2, '嗨', '你好啊')
    time.sleep(0.1)
    chatDB.insert('TqaBase', 3, 2, '再見', '改天見')
    time.sleep(0.1)
    chatDB.insert('TqaBase', 4, 1, '嗨', '很高興再見')
    print('1:',chatDB.select('TqaBase', channelID=1, userID=1, inmsg='嗨'))
    print('2:',chatDB.select('TqaBase', channelID=1, inmsg='嗨'))
    print('3:',chatDB.select('TqaBase', inmsg='嗨'))
    print('4:',chatDB.select('TqaBase', inmsg='你好'))
#    print(chatDB.select('TqaBase')
#    chatDB.delete('TqaBase')
#    print("After deleting data")
#    print(chatDB.select('TqaBase'))
'''