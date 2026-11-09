#!/usr/bin/env python
# -*- coding: latin-1  -*-

# Given the url of a flickr photo ti shows the url of the 'small' image
# Instagram:
# http://instagram.com/publicapi/oembed/?url=https://instagram.com/p/7rune8QB3W
# {"provider_url":"https:\/\/www.instagram.com","media_id":"1075157959480188374_30674102","author_name":"ftricas","height":null,"thumbnail_url":"https:\/\/scontent.cdninstagram.com\/hphotos-xaf1\/t51.2885-15\/s640x640\/sh0.08\/e35\/11934592_905119026244806_184077532_n.jpg","thumbnail_width":640,"thumbnail_height":640,"provider_name":"Instagram","title":"Gusano","html":"\u003cblockquote class=\"instagram-media\" data-instgrm-captioned data-instgrm-version=\"6\" style=\" background:#FFF; border:0; border-radius:3px; box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:658px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);\"\u003e\u003cdiv style=\"padding:8px;\"\u003e \u003cdiv style=\" background:#F8F8F8; line-height:0; margin-top:40px; padding:50.0% 0; text-align:center; width:100%;\"\u003e \u003cdiv style=\" background:url(data:image\/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAsCAMAAAApWqozAAAAGFBMVEUiIiI9PT0eHh4gIB4hIBkcHBwcHBwcHBydr+JQAAAACHRSTlMABA4YHyQsM5jtaMwAAADfSURBVDjL7ZVBEgMhCAQBAf\/\/42xcNbpAqakcM0ftUmFAAIBE81IqBJdS3lS6zs3bIpB9WED3YYXFPmHRfT8sgyrCP1x8uEUxLMzNWElFOYCV6mHWWwMzdPEKHlhLw7NWJqkHc4uIZphavDzA2JPzUDsBZziNae2S6owH8xPmX8G7zzgKEOPUoYHvGz1TBCxMkd3kwNVbU0gKHkx+iZILf77IofhrY1nYFnB\/lQPb79drWOyJVa\/DAvg9B\/rLB4cC+Nqgdz\/TvBbBnr6GBReqn\/nRmDgaQEej7WhonozjF+Y2I\/fZou\/qAAAAAElFTkSuQmCC); display:block; height:44px; margin:0 auto -44px; position:relative; top:-22px; width:44px;\"\u003e\u003c\/div\u003e\u003c\/div\u003e \u003cp style=\" margin:8px 0 0 0; padding:0 4px;\"\u003e \u003ca href=\"https:\/\/www.instagram.com\/p\/7rune8QB3W\/\" style=\" color:#000; font-family:Arial,sans-serif; font-size:14px; font-style:normal; font-weight:normal; line-height:17px; text-decoration:none; word-wrap:break-word;\" target=\"_blank\"\u003eGusano\u003c\/a\u003e\u003c\/p\u003e \u003cp style=\" color:#c9c8cd; font-family:Arial,sans-serif; font-size:14px; line-height:17px; margin-bottom:0; margin-top:8px; overflow:hidden; padding:8px 0 7px; text-align:center; text-overflow:ellipsis; white-space:nowrap;\"\u003eA photo posted by Fernando Tricas Garc\u00eda (@ftricas) on \u003ctime style=\" font-family:Arial,sans-serif; font-size:14px; line-height:17px;\" datetime=\"2015-09-16T07:33:58+00:00\"\u003eSep 16, 2015 at 12:33am PDT\u003c\/time\u003e\u003c\/p\u003e\u003c\/div\u003e\u003c\/blockquote\u003e\n\u003cscript async defer src=\"\/\/platform.instagram.com\/en_US\/embeds.js\"\u003e\u003c\/script\u003e","width":658,"version":"1.0","author_url":"https:\/\/www.instagram.com\/ftricas","author_id":30674102,"type":"rich"}
import html
import re, sys
from urllib.request import urlopen
from urllib.parse import urlparse
from urllib.parse import urlunparse
from bs4 import BeautifulSoup


def downloadUrl(url):

    page = urlopen(url).read()
    soup = BeautifulSoup(page,'lxml')
    res = []
    if (url.find('wordpress') >=0  
            or url.find('instagram') >= 0):
        foto = soup.find_all('meta', property="og:image")
        for image in foto:
            img = image['content']
            title = soup.find_all("meta",  property="og:title")[0]['content']
            alt = ''
            res.append((url,img,title,alt))
    #elif (url.find('imgur')>0):
    #    script = soup.find_all('script')
    #    #print(script[9])
    #    #print("****")
    #    #print(script[9].find_all('image'))
    #    pos = script[9].text.find('image')
    #    #print(pos)
    #    ##pos = script[9].text.find('image',pos+1)
    #    ##print(pos)
    #    pos = script[9].text.find('{',pos+1)
    #    #print(pos)
    #    pos2 = script[9].text.find('\n',pos+1)
    #    #print(pos2)
    #    #print('======')
    #    #print(script[9].text[pos:pos2-1])
    #    #print('======')
    #    import json
    #    data = json.loads(script[9].text[pos:pos2-1])
    #    #print('---')
    #    #print(data['album_images']['images'])
    #    title = data['title']
    #    #print(data)
    #    for img in data['album_images']['images']:
    #        #print("img %s" %img)
    #        #print(img['hash'])
    #        urlImg = 'https://i.imgur.com/{}.jpg'.format(img['hash'])
    #        if 'description' in img:
    #            titleImg = img['description']
    #        else:
    #            titleImg = img['description']
    #        res.append((url,urlImg,title, titleImg))
    elif url.find('flickr') >= 0:
        foto=soup.findAll('img',src=re.compile('.*static.*'))
        img = foto[-1]['src']
        title = soup.title.string.split('|')[0]
        alt = foto[-1]['alt'].split('|')[0]
        res.append((url,img,title,alt))
    elif url.find('facebook') >= 0:
        foto=soup.find_all('div', class_="hidden_elem")
        soup2=BeautifulSoup(foto[2].contents[0].contents[0])
        fotos = soup2.find_all('a', ajaxify=True)
        title = soup2.find_all('p')[0]

        for foto in fotos:
            urlF = foto['href'].split('&')[0]
            img = foto['data-ploi']
            if urlF.find('http')<0:
                urlF= 'https://facebook.com{}'.format(url)
            for i in foto.descendants:
                if 'get' in i.__dir__():
                    alt = i.get('alt')
                    if alt:
                        print(alt)
            res.append((urlF,img,title,alt))
    elif url.find('cactuseros')>=0:
        title = soup.find('title').findAll(text=True)[0]
        alt = title
        fotos = soup.find_all('img')
        for foto in fotos:
            img = foto['src']
            if 'class' in foto.attrs:
                theClass = foto['class'][0] 
                if (img.find('fernand0')>=0) and (theClass.find('width')>=0): 
                    res.append((url, img, title, alt))
    else:
        imgHtml = urlopen(url).read()
        soup = BeautifulSoup(imgHtml)
        img=soup.find_all("img")
        print(img)
        print("Don't know what to do")


    return res
        


def main():

    if len(sys.argv) == 0:
        print >>sys.stderr, USAGE
        sys.exit(1)

    url=sys.argv[1]

    res = downloadUrl(url)

    for (url, img, title, alt) in res:
        if not alt:
            alt=title
        print()
        print('<a href="{}" title="{}"><img src="{}" alt="{}" class="img-responsive img-centered"></a>'.format(url,title,img,alt))
        print()
        print('<a href="{}" title="{}"><img src="{}" alt="{}" width="240" style="float:left; margin:5px"></a>'.format(url,title,img,alt))
        print()

    sys.exit()



    downloadUrl(url)

    sys.exit()

    #url = 'https://www.instagram.com/p/B71l-QWFShk/'
    #url = 'https://www.facebook.com/groups/213771212055093/permalink/2629269607171896/'
    #url = 'https://www.facebook.com/alberto.virto.16/posts/10157988442670489'
    #url='https://avecesunafoto.wordpress.com/2020/02/09/creciendo/'
    #url='https://www.flickr.com/photos/fernand0/49511466712/in/dateposted/'
    #url = 'https://www.facebook.com/unaicampingciudaddezaragoza/posts/2730877406990974'


    #urlParsed = urlparse(url)
    #nick = urlParsed[2][len('photos')+2:]
    #pos = nick.find('/')
    #pos = pos + 1 + nick[pos+1:].find('/')
    #nick = nick[:pos]

    #print(nick)
    #url = urlunparse((urlParsed[0],urlParsed[1], 
    #    'photos/{}/sizes/s/'.format(nick),'','',''))
    #print(url)

    #downloadUrl(url)

    #url='https://avecesunafoto.wordpress.com/2020/02/09/creciendo/'

    #downloadUrl(url)

    #if len(sys.argv) == 0:
    #	print >>sys.stderr, USAGE
    #	sys.exit(1)
    #
    #url=sys.argv[1]
    #
    #imgs = []
    #urlTxt = []
    #if (url.find('flickr')>0):
    #    lenBase = len('https://www.flickr.com/photos/')
    #    start = url[lenBase+1:].find('/')
    #    endNick = url[lenBase+start:].find('/')
    #    end = url[lenBase+start+endNick+1:].find('/')
    #    
    #    urlSizes=url[:lenBase+start+end+1+1]
    #    
    #    
    #    flickrSizes = urlopen(urlSizes + '/sizes/s/')
    #    
    #    soupSizes = BeautifulSoup(flickrSizes)
    #    foto=soupSizes.findAll('img',src=re.compile('.*static.*'))
    #    urlTxt.append(urlSizes)
    #    fotoTxt = foto[-1]['src']
    #    imgs.append(fotoTxt)
    #    titleOrig = soupSizes.title.string
    #    pos = titleOrig.find('|')
    #    if pos >=0:
    #        titleOrig = titleOrig[pos+1:]
    #elif ((url.find('instagram')>0) 
    #        or (url.find('wordpress')>0) 
    #        or (url.find('imgur')>0)):
    #    if (url.find('?') > 0):
    #        url = url[:url.find('?')]
    #    imgHtml = urlopen(url).read()
    #    pos = imgHtml.find(b'og:image')
    #    pos1 = imgHtml.find(b'https', pos)
    #    pos2 = imgHtml.find(b'jpg', pos) + 3
    #    urlTxt.append(url)
    #    fotoTxt = imgHtml[pos1:pos2].decode('utf-8')
    #    print(fotoTxt)
    #    imgs.append(fotoTxt)
    #    # caption ?  
    #    if (url.find('wordpress')>0):
    #        soup = BeautifulSoup(imgHtml)
    #        titleOrig = soup.find("meta",  property="og:title")['content']
    #elif (url.find('facebook')>=0): 
    #    imgHtml = urlopen(url).read()
    #    soup = BeautifulSoup(imgHtml)
    #    divImg=soup.find_all("div", class_="hidden_elem")
    #    soup2=BeautifulSoup(divImg[2].contents[0].contents[0])
    #    print(soup2)
    #    sys.exit()
    #    listImg=soup2.find_all('img')
    #    urls=soup2.find_all('a', ajaxify=True)
    #    for i in urls:
    #        #print(i)
    #        iUrl=i['href'].split('&')[0]
    #        #print("--->",iUrl)
    #        #print(html.unescape(i['data-ploi']))
    #        #print(html.unescape(i['data-plsi']))
    #        imgs.append(html.unescape(i['data-ploi']))
    #        urlTxt.append(iUrl)
    #    #urlTxt=url
    #    #for cad in listImg[1:]:
    #    #    #print(cad)
    #    #    #print(html.unescape(cad['data-src']))
    #    #    imgs.append(html.unescape(cad['src']))
    #    #    #print("")
    #        titleOrig = None
    #else:
    #    imgHtml = urlopen(url).read()
    #    soup = BeautifulSoup(imgHtml)
    #    img=soup.find_all("img")
    #    print(img)
    #
    #if titleOrig: 
    #    title=input("Campo title: (Orig: %s)"%titleOrig)
    #else:
    #    title=input("Campo title: ")
    #if title=="":
    #    title = titleOrig
    #    alt = titleOrig
    #else: 
    #    alt=input("Campo alt (Vacío para poner el mismo): ") 
    #    if (alt==""):
    #        alt=title
    #
    #for i,fotoTxt in enumerate(imgs):
    #    print('<a href="%s" title="%s"><img src="%s" alt="%s" class="img-responsive img-centered" width="240" style="float:left; margin:5px"></a>'%(urlTxt[i],title,fotoTxt,alt))
    #    print()
    #    #print("--------------------------")
    #    #print(urlTxt)
    #    #print(fotoTxt)

if __name__ == '__main__':
    main()
