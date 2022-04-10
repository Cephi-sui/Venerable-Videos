import urllib.request, urllib.error, urllib.parse
import argparse
import re

import psycopg2

from archive_video import *

#Obtains video name, creator id, and creator name from the specified video url
def examine_video(url):
    #Get and parse html
    response = urllib.request.urlopen(url)
    webpage = response.read().decode('UTF-8')
    lines = webpage.splitlines()

    video_name = ""
    creator_id = ""
    creator_name = ""

    #Search for video name, creator id, and creator name
    for line in lines:
        if "meta itemprop=\"name\" content=" in line: #get video name
            video_name = re.findall(r'meta itemprop=["]name["] content=["](.*?)["]', line)[0]
            
        if "link itemprop=\"name\" content=" in line: #get creator name
            creator_name = re.findall(r'link itemprop=["]name["] content=["](.*?)["]', line)[0]

        #Had to handle three possible channel links
        if re.search(r'link itemprop=["]url["] href=["]http.?://www.youtube.com/(channel/|c/|user/)(.*?)["]', line) != None: #get creator_id (channel link)
            creator_id = re.findall(r'link itemprop=["]url["] href=["]http.?://www.youtube.com/(channel/|c/|user/)(.*?)["]', line)[0][1]
            #findall above produces a tuple inside a list because of the or in regex, hence [0][1]

    return (video_name, creator_id, creator_name)

#Preps database with videos and creators tables if not already existing
def prepare_db(connection):
    with connection.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS videos (id STRING PRIMARY KEY, name STRING,\
        creator_id STRING NOT NULL, creator_name STRING, url STRING, mirror STRING)")

        cur.execute("CREATE TABLE IF NOT EXISTS creators (id STRING PRIMARY KEY, name STRING, mirror STRING)")

    connection.commit()

#Inserts video with specified information into database
def insert_video(connection, video_id, video_name, creator_id, creator_name, video_link, creator_mirror = None):
    if creator_mirror is not None:
        video_mirror = creator_mirror + "/" + video_id + ".mp4"
    else:
        creator_mirror = None
        video_mirror = None
    
    #Insert video into videos table and creator into creators tables (if not found)
    #Would like to add creator_url functionality in future.
    with connection.cursor() as cur:
        cur.execute("UPSERT INTO videos (id, name, creator_id, creator_name, url, mirror) VALUES (%s, %s, %s, %s, %s, %s)",\
                     (video_id, video_name, creator_id, creator_name, video_link, video_mirror))
        print((video_id, video_name, creator_id, creator_name, video_link, video_mirror))
        cur.execute("UPSERT INTO creators (id, name, mirror) VALUES (%s, %s, %s)", (creator_id, creator_name, creator_mirror))
        print((creator_id, creator_name, creator_mirror))

    #Reserve commit for after archive_video(), in case error is thrown
    #connection.commit()

def main():
    #Parses arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("max_vids", type=int, help="Maximum number of videos to store")
    parser.add_argument("url", type=str, help="The URL of the YouTube page to search")
    parser.add_argument("connect", type=str, help="The string required to connect to CockroachDB")
    parser.add_argument("dlpath", type=str, help="The directory to store archives")

    args = parser.parse_args()

    #Can add cases to add support for another websites/platforms
    keyword = ""
    base_url = ""
    regex_key = r''
    if "youtube" in args.url:
        keyword = "/watch?"
        base_url = "https://www.youtube.com"
        regex_key = r'/watch[?]v=(.*)'
    else: #Else the url passed is not supported, exit
        print("Non-YouTube links are currently not supported")
        exit()

    max_vids = args.max_vids

    #Get and parse html
    response = urllib.request.urlopen(args.url)
    webpage = response.read().decode('UTF-8')
    lines = webpage.splitlines()
    videos = set()

    #Connect to CockroachDB
    connection = psycopg2.connect(args.connect)
    prepare_db(connection)

    #If link is a single video
    if keyword in args.url:
        videos.add(re.search(regex_key, args.url).group())
    else: #Else link is a channel
        counter = 0
        for line in lines: #For every line of HTML, find a link with keyword and add to the set videos
            if keyword in line: #Don't regex line if won't have link
                quotes = re.findall(r'["](.*?)["]', line) #Check every keyword in ""
                for quote in quotes: #For every keyword in ""
                    if keyword in quote and "list" not in quote: #Check if it is a video link (and not a playlist)
                        videos.add(quote) #If it is a video link, add it to videos

                        counter = counter + 1
                        if counter >= max_vids:
                            break
                    
    for video_path in videos: #For every video found, print the link, get the data, and insert the data into the database
        video_link = base_url + video_path #Turn the id into a full link
        video_id = re.findall(regex_key, video_link)[0]
        print(video_link) #Print the video link
        vid_data = examine_video(video_link) #Get the video data
        #creator_mirror = args.dlpath + "/" + vid_data[2]
        
        insert_video(connection, video_id, vid_data[0], vid_data[1], vid_data[2], video_link) #Insert the video data into the database
        #archive_video(video_link, video_id, creator_mirror)

    connection.commit()
    connection.close()
    
if __name__ == "__main__":
    main()
