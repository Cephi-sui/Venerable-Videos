import argparse

import psycopg2

from main import *

def video_name_query(connection, query):
    like = "%" + query + "%" #Grab any name with query in it
    
    with connection.cursor() as cur:
        cur.execute("SELECT name, creator_name, url, mirror FROM videos WHERE name ILIKE (%s)", (like,)) #Case insensitive

        rows = cur.fetchall() #Puts all output into rows

    connection.commit()

    print_query(rows)

def creator_name_query(connection, query):
    like = "%" + query + "%"

    with connection.cursor() as cur: #Does the same as video_name_query, but grabs all videos associated with a creator
        cur.execute("SELECT creators.name, videos.name, videos.url, videos.mirror FROM creators \
        INNER JOIN videos ON creators.id = videos.creator_id WHERE creators.name ILIKE (%s)", (like,))

        rows = cur.fetchall()

    connection.commit()

    print_query(rows)

def print_query(query_rows):
    name_size = 30
    c_name_size = 30
    url_size = 50
    formatted = "{:<"+str(name_size)+"}|{:<"+str(c_name_size)+"}|{:<"+str(url_size)+"}|{}" #formatting the column widths
    columns = ("name", "creator_name", "url", "mirror")
    print(formatted.format(columns[0], columns[1], columns[2], columns[3])) #printing column titles
    for e1, e2, e3, e4 in query_rows: #this mess truncates strings and appends ".." if too long for the column
        e1 = e1[:(name_size-2)] + (e1[(name_size-2):] and '..')
        e2 = e2[:(c_name_size-2)] + (e2[(c_name_size-2):] and '..')
        e3 = e3[:(url_size-2)] + (e3[(url_size-2):] and '..')
        print(formatted.format(e1,e2,e3,e4))
        
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", type=str, help="What you want to search. Either video=[video-name] or creator=[creator-name]")
    parser.add_argument("connect", type=str, help="The string required to connect to CockroachDB")

    args = parser.parse_args()

    connection = psycopg2.connect(args.connect)
    
    prepare_db(connection)

    #Parse query and execute if valid
    if re.search(r'^video=', args.query) is not None:
        query = re.findall(r'video=(.*)', args.query)[0]
        video_name_query(connection, query)
    elif re.search(r'^creator=', args.query) is not None:
        query = re.findall(r'creator=(.*)', args.query)[0]
        creator_name_query(connection, query)
    else:
        print("Not a valid query!")
        exit()

if __name__ == "__main__":
    main()
