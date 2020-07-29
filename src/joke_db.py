#/usr/bin/env python
# -*- coding: utf-8 -*-
# Written by Sam Tseng on 2018/12/07, copy from Chat_DB.py
# Currently SQLite3 is used
# To use MySQL, see: https://blog.gtwang.org/programming/python-mysqldb-connect-mysql-database-tutorial/
# Add word2vec on 2019/09/04
#	python joke_db.py 0.3 Chat_DB.db

import sqlite3
import sys, time
import sys, re
#import Next_Doc
import jieba
import gensim
from gensim import corpora, models, similarities
from gensim.models.keyedvectors import KeyedVectors
# jieba.load_userdict("userdict.txt") # will use self-built dict.
import jieba.analyse
#jieba.set_dictionary('TermFreq-utf8.txt') # did not work on 2015/10/21
#jieba.add_word('壞人');jieba.add_word('細菌'); # did not work


#StopList = u'的 是 有 在 或 來 從 此 因 且 為 他 嗎 那 哪 吧 很 它 這 我 於'.split()
#StopList.extend(u'⒈ ⒉ ⒊ 可能 應該 則是 它會 這麼 什麼 他們 因為 那些 圖上'.split())
StopList = ""
#model = gensim.models.Word2Vec.load(".\word2vec\wiki.zh.model")
model =KeyedVectors.load("./word2vec/wiki.zh.model")
synonym = model.wv.most_similar("睡著",topn=5)

class joke_db():
    '''
    Given a file containing multiple documents in CSV format,
    return a document each time nextdoc() is called.
    So far this class is only for the download CSV format from CCR
    '''
    def __init__(self, InFile='Chat_DB.db', DBis='SQLite'):
        self.InFile = InFile
        self.dbFile = InFile
        self.DBis = DBis
        '''
		if DBis == 'SQLite':
			self.conn = sqlite3.connect(InFile)
		
        else:
            sys.stderr.write('Please specify a database, like SQLite, MySQL, ...')
        cur = self.conn.cursor()
		'''

    def __del__(self):
        #self.conn.close()
        pass

    def IndexingTerms(self, words):
    # Below, we remove punctuations and stopwords:
    	text = []
    	for word in words:  
    #		isCMark = re.search(u' |，|。|；|？|、|：|（|）|！|~', word)
    #		isEMark = re.search(r',|\.|;|:|\?|\(|\)|\!|\d', word)
    #		isEMark = re.search(r'[\.,;\:\?\(\)\!\'\"=\-\+\d]', word) # '""
    #		if ((isCMark is None) and (isEMark is None) 
    #			and (not re.match(r'\W', word))
    #			and (word not in StopList)):
    		if (not re.match(r'\W', word)):
    			text.append(word)
    	return text

# remove words that appear only once
    def RemoveLowTerms(self, texts):
    	from collections import defaultdict
    	frequency = defaultdict(int)
    	for text in texts:
    	    for token in text:
    	        frequency[token] += 1
    	texts = [[token for token in text if frequency[token] > 1]
    			for text in texts]
    	#pprint(texts); print()
    	return texts

    def OutputSimilarPairs(self, index, sim_threshold, org_texts):
    	NumSimPairs = 0
    #	for i, vec in enumerate(corpus_tfidf):
    		#sims = index[vec]
    	for i, sims in enumerate(index): # https://radimrehurek.com/gensim/similarities/docsim.html
    		#print(sims)
    		sims = sorted(enumerate(sims), key=lambda item: -item[1])
    		#print(sims) # print sorted (document number, similarity score) 2-tuples
    		for (docID, sim) in sims:
    			if sim > sim_threshold and i < docID:
    				print("\n%d\t%d\t%1.2f"%(i, docID, sim))
    				print(i, ':', org_texts[i])
    				print(docID, ':', org_texts[docID])
    				NumSimPairs += 1
    			elif sim < sim_threshold:
    				break
    	sys.stderr.write("There are %d pairs\n" % NumSimPairs)

    def SetTexts(self):
		#nxtd = Next_Doc.Next_Doc(InFile=self.InFile)
    	self.conn = sqlite3.connect('Chat_DB.db')
    	cur = self.conn.cursor()
    	cur.execute("SELECT jokeID, txt FROM TjokeBase")
    	W = cur.fetchall()
    	i = 0
    	self.org_texts = []
    	self.texts = []
		
    	for index in range(len(W)):
    		source = W[index][0] 
    		joke = W[index][1]

    		#UserID[i] = (email, content)
    		i += 1
    		#print("%d : %s : %s\n" % (i, email, content))
    		self.org_texts.append(joke)
    		words = jieba.cut(joke, cut_all=False) # see https://github.com/fxsjy/jieba
    #  Choose to remove stopwors or not:
    #		text = [word for word in words] # this line preserves all tokens
    		text = self.IndexingTerms(words) # this remove stopwords and punctuations
    		self.texts.append(text)
    	sys.stderr.write("There are %d documents\n" % i)
    	#return(org_texts, texts)

    def MakeIndex(self):
	    self.dictionary = corpora.Dictionary(self.texts)
	    sys.stderr.write("Number of tokens:%d\n" % len(self.dictionary))
	    self.NumTokens = len(self.dictionary)
	    self.corpus = [self.dictionary.doc2bow(text) for text in self.texts]

	    self.tfidf = models.TfidfModel(self.corpus, normalize=True)
	    self.corpus_tfidf = self.tfidf[self.corpus]
	    self.index = similarities.SparseMatrixSimilarity(self.corpus_tfidf, num_features=self.NumTokens)

    def GetSimilarText(self, inp, sim_threshold):
    	inp = inp.strip()
    	new = self.dictionary.doc2bow(self.IndexingTerms(jieba.cut(inp)))
    	word = self.IndexingTerms(jieba.cut(inp))[0]
    	words = []
    	try:
    		synonym = model.wv.most_similar(word, topn=10)
    		for index in range(len(synonym)):
    			relatedwords = synonym[index][0]
    			words.append(relatedwords)
    	except:
    		synonym = [(word, 1.0)]

    	#print(words[0]+' '+words[1]+' '+words[2]+' '+words[3]+' '+words[4]+' '+words[5]+' '+words[6]+' '+words[7]+' '+words[8]+' '+words[9])

    	new_tfidf = self.tfidf[new]
    	sims = self.index[new_tfidf]
    	new_words = self.tfidf[self.dictionary.doc2bow(words)]
    	sims_words = self.index[new_words]
    	sims = sims + sims_words
    	sims = sorted(enumerate(sims), key=lambda item: -item[1])
    	print(sims[:3]) # print sorted (document number, similarity score) 2-tuples
    	SimTexts = []
    	for (docID, sim) in sims:
    		if sim > sim_threshold: # append a triple
    			SimTexts.append((docID, sim, self.org_texts[docID]))
    			#print("\n%d\t%1.2f"%(docID, sim), self.org_texts[docID])
    	return SimTexts

if __name__ == "__main__":
	# python joke_db.py 0.3 Chat_DB.db
	
	(sim_threshold, DocFile) = (sys.argv[1], sys.argv[2])
	sim_threshold = float(sim_threshold) 
	print(len(sys.argv), sim_threshold, DocFile)
	jdb = joke_db(InFile=DocFile)
	jdb.SetTexts()
	jdb.MakeIndex()
	
	while(True):
		synonym = model.wv.most_similar("睡著", topn=10)
		inp = input("Enter a query string: ")
		#words = []
		#synonym = model.wv.most_similar(inp, topn=10)
		#for index in range(len(synonym)):
		#	relatedwords = synonym[index][0]
		#	words.append(relatedwords)
		#i = 0 
		#for index in range(len(words)):
		#	print(words[i]+' ')
		#	i += 1
		#print(words[0]+' '+words[1]+' '+words[2]+' '+words[3]+' '+words[4]+' '+words[5]+' '+words[6]+' '+words[7]+' '+words[8]+' '+words[9])
		SimTexts = jdb.GetSimilarText(inp, sim_threshold)
		for	DocID, sim, SimText in SimTexts:
			print(DocID, sim, SimText)
