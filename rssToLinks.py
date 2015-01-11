#!/usr/bin/python

# 
# This program reads a feed an extracts its entries and the links they contain
# The idea is to have for each entry a list of the links at the end.
# Each entry contains the text and a list of links. In the text there are
# numbers in [x] for each link that reference the corresponding link at the
# end. It has no HTML markup.

import feedparser, re
from bs4 import BeautifulSoup
from bs4 import NavigableString
from bs4 import Tag

url='https://fernand0.github.io/feed.xml' # Put your RSS feed here

feed = feedparser.parse(url)

for i in range(len(feed.entries)):
	soup = BeautifulSoup(feed.entries[i].summary)
	links = soup("a")
	
	j = 0
	linksTxt = ""
	for link in links:
		if not isinstance(link.contents[0], Tag):
			# We want to avoid embdeded tags (mainly <img ... )
			link.append(" ["+str(j)+"]")
			linksTxt = linksTxt + "["+str(j)+"] " + link.contents[0] + "\n"
			linksTxt = linksTxt + "    " + link['href'] + "\n"
			j =  j + 1
	print "Entry "+str(i)+":"
	print soup.get_text()
	if linksTxt != "":
		print
		print "Links :"
		print linksTxt
	print
