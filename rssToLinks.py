#!/usr/bin/python

# 
# This program reads a feed an extracts the entries and the links they contain
# The idea is to have for each entry a list of the links at the end.
# Each entry contains numbers in [x] and the number refers to the corresponding
# link at the end. It has no HTML markup.
# 

import feedparser, re
from bs4 import BeautifulSoup
from bs4 import NavigableString
from bs4 import Tag

url='https://github.com/fernand0.atom'
url='http://fernand0.tumblr.com/rss'

feed = feedparser.parse(url)

for i in range(len(feed.entries)):
	soup = BeautifulSoup(feed.entries[i].summary)
	links = soup("a")
	
	j = 0
	linksTxt = ""
	for link in soup("a"):
		# print type(link.contents[0])
		if not isinstance(link.contents[0], Tag):
			# We want to avoid embdeded tags (mainly <img ... )
			if not re.search(r"delicious.*fernand0.*rei", link['href']):
				# We want to avoid tags in fernand0.blogalia.com
				link.append(" ["+str(j)+"]")
				j =  j + 1
				linksTxt = linksTxt + "["+str(j)+"] " + link.contents[0] + "\n"
				linksTxt = linksTxt + "    " + link['href'] + "\n"
	print "Entry "+str(i)+":"
	print soup.get_text()
	if linksTxt != "":
		print "Links :"
		print linksTxt
	print
