import pymongo
from bson import ObjectId, json_util

client = pymongo.MongoClient()

db = client.lyric
songs = db.songs

def getSongFromID(id):
    return songs.find_one({ '_id': ObjectId(id) })

def getSongList():
    return list(songs.find())