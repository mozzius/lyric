import pymongo
from bson import ObjectId, json_util

client = pymongo.MongoClient()

db = client.lyric
songs = db.songs
collections = db.collections


def getSongFromID(id):
    song = songs.find_one({'_id': ObjectId(id)})
    return {'song': song, 'collection': getCollectionFromID(song['collection_id'])}


def getSongsFromCollectionID(collection_id):
    return list(songs.find({'collection_id': collection_id}))


def getSongList():
    return list(songs.find())


def getCollectionFromID(id):
    return collections.find_one({'_id': ObjectId(id)})


def getCollectionList():
    return list(collections.find())


def getCollectionsWithSongs():
    collections = []
    for collection in getCollectionList():
        collections.append(
            {
                '_id': collection['_id'],
                'title': collection['title'],
                'image': collection['image'],
                'songs': getSongsFromCollectionID(collection['_id']),
            }
        )
    return collections

def addSong(song):
    assert song['title']
    assert song['collection_id']
    assert song['lyrics']
    assert songs.find({ 'title': song['title'], 'collection_id': ObjectId(song['collection_id']) }).count == 0
    song['collection_id'] = ObjectId(song['collection_id'])
    song['lyrics'] = song['lyrics'].replace('\n', ' ')
    return songs.insert_one(song).inserted_id