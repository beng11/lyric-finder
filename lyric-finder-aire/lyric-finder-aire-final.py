import math
from bs4 import BeautifulSoup
import requests
import re
import time
import random as r
import sys
import statistics as stat

# VPN IS ADVISED TO AVOID POSSIBILITY OF BEING BLOCKED BY AZLYRICS.COM
# MEASURES HAVE BEEN TAKEN TO REDUCE LIKELIHOOD OF BLOCKING

# get inputs
artist = input("Artist name:")
print("There are two methods of accessing lyric content in this script")
print("Either select a lyric API (lyricsovh.docs.apiary.io), or a web scraping method")
print("to prevent possible blocking of AZlyrics.com, only use 'scrape' method with a VPN")
print("api method is slower but reliable. scrape method is quicker but can be inconsisent")
method = input("Method (api/scrape):")

# a list of valid user agents (crawlers and browsers) to rotate through.
user_agents=[
'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',
'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36 OPR/63.0.3368.107', #opera
'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)',
'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14931', # edge
'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201',
'Mozilla/5.0 (Windows NT 5.1; rv:11.0) Gecko Firefox/11.0 (via ggpht.com GoogleImageProxy)',
'Gigabot/3.0 (http://www.gigablast.com/spider.html)',
'genieBot (http://64.5.245.11/faq/faq.html)',
'end'
]

cont = True

print("starter agent: "+user_agents[0])

my_headers={
    'User-Agent':user_agents[0]
}

n=0
lyric_sum=0
song_lengths = []
song_names = []

try: # access the artists page on AZ lyrics for a full list of song names
    page = requests.get("https://search.azlyrics.com/search.php?q="+artist,headers=my_headers)
except: # in case of exception, remove current user agent and try again
    user_agents.pop(0)
    my_headers={'User-Agent':user_agents[0]}
    if user_agents[0]=="end":
        sys.exit("program terminated")
    else:
        try: # send request with new agent
            page = requests.get("https://search.azlyrics.com/search.php?q="+artist,headers=my_headers)
        except: # in case of second failure, terminate
            sys.exit("program terminated due to bad agent")


# find the tag containing the artist html
soup_page = BeautifulSoup(page.content,'html.parser')
artist_link = soup_page.find('td',class_='text-left visitedlyr')

# a messy way to get the html line from soup
i=0
for line in artist_link:
    i+=1
    artist_link = str(line)
    if i==2:
        break

# retrieve only the html link
artist_link = re.search(r'\"(.+?)\"',artist_link).group(0)[1:-1]

# use artist link
try:
    artist_page = requests.get(artist_link,headers=my_headers)
except:
    user_agents.pop(0)
    my_headers={'User-Agent':user_agents[0]}
    if user_agents[0]=="end":
        print("To protect from blocking, code is terminated.")
    else:
        try:
            artist_page = requests.get(artist_link,headers=my_headers)
            print("new agent")
        except:
            sys.exit("program terminated due to bad agent")

soup_page = BeautifulSoup(artist_page.content,'html.parser')

# extract all href tags
soup_page = soup_page.findAll('a')
r.shuffle(soup_page)


for each in soup_page: # remove non-song a-tags and remix versions of songs
    if not str(each).startswith('<a href="https://www.azlyrics') and not str(each).startswith('<a href="../lyrics'):
        soup_page.remove(each)
    elif str(each).find('remix')!=-1:
        soup_page.remove(each)
        
for each in soup_page:
    each = re.sub('&amp;', "and",str(each))
    if str(each).startswith('<a href="https://www.azlyrics') or str(each).startswith('<a href="../lyrics'): # whole request
        each = re.sub(r'\((.+?)\)', "",str(each))
        song_names.append(str(re.findall(r'\>(.+?)\<',str(each))))

# retrieve, count and perform operations on lyrics
def lyric_counter(each,my_headers,user_agents,lyric_sum,n):
    global cont

    if n%76==0 and n!=0:
        user_agents.pop(0)
        my_headers={'User-Agent':user_agents[0]}
        song_page = requests.get(each,headers=my_headers)
        print("preparing new agent: "+user_agents[0])
    else:
        try:
            song_page = requests.get(each,headers=my_headers)
        except:
            user_agents.pop(0)
            my_headers={'User-Agent':user_agents[0]}
            try:
                song_page = requests.get(each,headers=my_headers)
                print("preparing new agent: "+user_agents[0])
            except:
                cont = False
                return lyric_sum            
    
    each = str(each)[24:] # remove the http portion
    
    # find appropriate portion of lyrics page
    lyric_soup_page = BeautifulSoup(song_page.content,'html.parser')
    lyric_soup_page = lyric_soup_page.findAll('div')

    song_lyrics = []

    # 12th div contains lyrics
    i=10
    for chunk in lyric_soup_page[14]:
        if str(chunk).startswith("<div>\n<!--"):
            lyric_chunk = chunk

    # remove unwanted artifacts - tags, producer credits, backing vocals etc
    lyric_chunk = re.sub(r'\<(.+?)\>', "",str(lyric_chunk))
    lyric_chunk = re.sub(r'\[(.+?)\]', "",str(lyric_chunk))
    lyric_chunk = re.sub(r'\((.+?)\)', "",str(lyric_chunk))
    
    # get the song word length and add to total
    song_length = len(lyric_chunk.split())
    lyric_sum += song_length
    song_lengths.append(song_length)
    
    print("song number "+str(n)+" with id of "+str(each)[8:-5]+" has "+str(song_length) + " words.")

    return lyric_sum

if method.lower() == "scrape": # web scraping method

    for each in soup_page:
        if cont == True:
            n+=1
            if str(each).startswith('<a href="https://www.azlyrics'): # whole request
                each = re.search(r'\"(.+?)\"',str(each)).group(0)[1:-1]
                lyric_sum = lyric_counter(each,my_headers,user_agents,lyric_sum,n)

            elif str(each).startswith('<a href="../lyrics'): # request with added url
                each = re.search(r'\"(.+?)\"',str(each)).group(0)[3:-1]
                each = "https://www.azlyrics.com"+each
                lyric_sum = lyric_counter(each,my_headers,user_agents,lyric_sum,n)

elif method.lower()=="api": # api method
    for song in song_names:
        n+=1
        song = song[2:-2]
        try:
            lyrics = requests.get("https://api.lyrics.ovh/v1/"+artist+"/"+song)
            if lyrics.content != "No lyrics found" and len(lyrics.content.split())>3:
                song_length = len(lyrics.content.split())
                lyric_sum += song_length
                song_lengths.append(song_length)
                print("{} has {} words in it".format(song,str(song_length)))
            else:
                print("failed to find song {}".format(song))
        except:
            print("failed to find song {}".format(song))
else:
    sys.exit("please choose a valid method")

# perform calculations on lyric data
if lyric_sum==0 or song_lengths==[]:
    print("failed to find any songs for "+artist)
else:
    song_length_average = int(lyric_sum/(n))
    song_lengths.sort()
    print("--------------------------------")
    print("Collated a total of {} songs, which is {} percent of {}'s discography".format(str(n),str(int(100*n/len(soup_page))),artist))
    print(artist+" has an average lyric count of "+str(song_length_average))
    print(artist+"'s shortest song is "+str(song_lengths[0])+" words and the longest is "+str(song_lengths[-1]))
    print("The {} method was used".format(method))
    artist_file = open('artist_averages.txt','a+')
    artist_file.write("\n"+artist+" : "+str(song_length_average)+" ({})".format(method))
    artist_file.close()
    