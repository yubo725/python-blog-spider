#coding: utf-8
from bs4 import BeautifulSoup
import MySQLdb
import urllib2
import hashlib
import base64
import re

# 文章类
class Article:
	def __init__(self, id, title, brief, time, readcount, commentcount, detailurl):
		self.id = id
		self.title = title
		self.brief = brief
		self.time = time
		self.readcount = readcount
		self.commentcount = commentcount
		self.detailurl = detailurl

# 连接数据库
def getConnection():
	conn = MySQLdb.connect('localhost', 'root', 'root', 'blog', charset='utf8')
	conn.set_character_set('utf8')
	return conn;

# 获取字符串的MD5
def getMD5(str):
	md5 = hashlib.md5()
	md5.update(str)
	return md5.hexdigest()

# 获取某个文章的标题和详情链接
def getTitleAndDetail(item):
	e = item.find('a')
	if e != None:
		title = e.string
		detailurl = 'http://blog.csdn.net%s' % e['href']
		return {"title": title, "detailurl": detailurl}
	return None

# 获取某个文章的摘要
def getBrief(item):
	e = item.find(class_="article_description")
	if e != None:
		return e.string
	return ""

# 获取某个文章的阅读数
def getReadCount(item):
	e = item.find(class_="link_view")
	if e != None:
		text = e.get_text()
		if text != None:
			return int(text[3:len(text) - 1])
	return 0

# 获取某个文章的评论数
def getCommentCount(item):
	e = item.find(class_="link_comments")
	if e != None:
		text = e.get_text()
		return int(text[3:len(text) - 1])
	return 0

# 获取某个文章的时间
def getTime(item):
	e = item.find(class_="link_postdate")
	if e != None:
		return e.string
	return 0

# 获取总页数
def getPageSize(content):
	div = content.find(id="papelist")
	if div != None:
		span = div.find('span').get_text()
		if span != None:
			pattern = re.compile('\d+')
			match = pattern.findall(span)
			if match and len(match) > 1:
				return int(match[1])
	return 0

# 判断某个id对应的文章是否在数据库中
def isRecordExist(id):
	sql = "select * from article where id = '%s'" % id
	conn = getConnection()
	cursor = conn.cursor()
	cursor.execute(sql)
	data = cursor.fetchall()
	cursor.close();
	return len(data) > 0

# 数据库插入一条记录
def saveRecord(article):
	if isinstance(article, Article):
		if not isRecordExist(article.id):
			title = base64.b64encode(article.title)
			brief = base64.b64encode(article.brief)
			sql = "insert into article(id, title, brief, time, readcount, commentcount, detailurl) values('%s', '%s', '%s', '%s', %d, %d, '%s')" % (article.id, title, 
				brief, article.time, article.readcount, article.commentcount, article.detailurl)
			print 'sql =', sql
			conn = None
			cursor = None
			try:
				conn = getConnection()
				cursor = conn.cursor()
				cursor.execute(sql)
				conn.commit()
				print 'insert into db success'
			except Exception as e:
				print 'insert into db error: ', e
			finally:
				if conn != None:
					conn.close()
				if cursor != None:
					cursor.close()
		else:
			print 'record exist!'

# 获取某一页的数据
def getPageData(soup):
	listElement = soup.find(id='article_list')
	articalList = listElement.find_all(class_="list_item article_item")
	for item in articalList:
		dic = getTitleAndDetail(item)
		title = dic['title']
		detailurl = dic['detailurl']
		brief = getBrief(item)
		time = getTime(item)
		readcount = getReadCount(item)
		commentcount = getCommentCount(item)
		id = getMD5('%s%s' % (title, time))
		article = Article(id, title, brief, time, readcount, commentcount, detailurl)
		saveRecord(article)

def start(url):
	response = urllib2.urlopen(url)
	content = response.read()
	soup = BeautifulSoup(content, 'html.parser')
	getPageData(soup)
	pageSize = getPageSize(soup)
	if pageSize > 1:
		for index in range(2, pageSize + 1):
			urlStr = '%s/article/list/%d' % (url, index)
			print 'url =', urlStr
			getPageData(BeautifulSoup(urllib2.urlopen(urlStr).read(), 'html.parser'))

# 删除数据库所有数据
def deleteAll():
	sql = 'delete from article where 1 = 1'
	conn = getConnection()
	cursor = conn.cursor()
	cursor.execute(sql)
	conn.commit()
	cursor.close()
	conn.close()

if __name__ == '__main__':
	# deleteAll()
	start('http://blog.csdn.net/yubo_725')
