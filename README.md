# Venerable-Videos
Ever wanted to automatically take a webpage full of videos and store the data in a database?

Probably not. But here it is anyway!

##Dependencies
- python3
- psycopg2
- CockroachDB

## How to Use
For getting video data:
```
python3 main.py [num_max_videos] [link] [CockroachDB connection string] [download directory]
```

For basic database querying:
```
python3 query-db.py [video={video_name} OR creator={creator_name}] [CockroachDB connection string]
```
