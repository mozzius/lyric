from bson import ObjectId, json_util
import pymongo
import re
import hashlib
import bleach
import datetime

try:
    from main import current_user
except ImportError:
    from app.main import current_user

client = pymongo.MongoClient()

db = client.lyric
songs = db.songs
collections = db.collections
users = db.users
rooms = db.rooms


def getSongFromID(id):
    song = songs.find_one({"_id": ObjectId(id)})
    return {"song": song, "collection": getCollectionFromID(song["collection_id"])}


def getSongsFromCollectionID(collection_id):
    return list(songs.find({"collection_id": collection_id}))


def getSongList():
    return list(songs.find())


def getCollectionFromID(id):
    return collections.find_one({"_id": ObjectId(id)})


def getCollectionList():
    return list(collections.find())


def getCollectionWithSongsFromID(id):
    collection = getCollectionFromID(id)
    return {
        "_id": collection["_id"],
        "user_name": getUser(collection["user_id"])["username"],
        "title": collection["title"],
        "image": collection["image"],
        "songs": getSongsFromCollectionID(collection["_id"]),
    }


def getCollectionsWithSongs():
    collections = []
    for collection in getCollectionList():
        collections.append(
            {
                "_id": collection["_id"],
                "user_name": getUser(collection["user_id"])["username"],
                "title": collection["title"],
                "image": collection["image"],
                "songs": getSongsFromCollectionID(collection["_id"]),
            }
        )
    return collections


def addSong(song):
    assert song["title"]
    assert song["collection_id"]
    assert song["lyrics"]
    assert song["user_id"]
    assert (
        songs.find(
            {"title": song["title"], "collection_id": ObjectId(song["collection_id"])}
        ).count()
        == 0
    )
    song["collection_id"] = ObjectId(song["collection_id"])
    song["lyrics"] = song["lyrics"].replace("\n", " ")
    song["date"] = datetime.datetime.utcnow()
    return songs.insert_one(song).inserted_id


def addCollection(collection):
    assert collection["title"]
    assert collection["image"]
    assert collection["user_id"]
    assert collections.find({"title": collection["title"]}).count() == 0
    collection["date"] = datetime.datetime.utcnow()
    return collections.insert_one(collection).inserted_id


# MULTIPLAYER STUFF


def createRoom(name, song_id):
    assert name
    assert song_id
    assert rooms.find({"name": name}).count() == 0
    room = {
        "name": name,
        "song_id": song_id,
        "members": [
            {
                "id": current_user.get_id(),
                "username": current_user.username,
                "numerator": 0,
                "denominator": 0,
            }
        ],
    }
    return rooms.insert_one(room).inserted_id


def joinRoom(name):
    room = rooms.find_one({"name": name})
    if room != None:
        for member in room["members"]:
            if current_user.get_id() == member["id"]:
                return room

        rooms.update(
            {"_id": room["_id"]},
            {
                "name": room["name"],
                "song_id": room["song_id"],
                "members": room["members"]
                + [
                    {
                        "id": current_user.get_id(),
                        "username": current_user.username,
                        "numerator": 0,
                        "denominator": 0,
                    }
                ],
            },
        )
        return rooms.find_one({"_id": ObjectId(room["_id"])})
    else:
        return None


def getRoom(id):
    return rooms.find_one({"_id": ObjectId(id)})


def getRoomMembers(id):
    return getRoom(id)["members"]


def leaveRoom(user_id):
    room = rooms.find_one({"members.id": user_id})
    rooms.update(
        {"_id": room["_id"]},
        {
            "name": room["name"],
            "song_id": room["song_id"],
            "members": [x for x in room["members"] if x["id"] != user_id],
        },
    )
    return rooms.find_one({"_id": room["_id"]})


def deleteRoom(id):
    rooms.remove({"_id": ObjectId(id)})


# USER STUFF


def sha256(msg):
    return hashlib.sha256(msg.encode("utf-8")).digest()


def addUser(name, email, password):
    # cleaning inputs
    name = bleach.clean(name)
    match = re.match(
        "^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$", email
    )
    password = sha256(password)
    try:
        assert match
        assert name != ""
        assert users.find({"email": email}).count() == 0
        assert users.find({"username": name}).count() == 0
        user_id = users.insert_one(
            {"username": name, "email": email, "password": password}
        ).inserted_id
    except Exception as e:
        print(e)
        return None
    else:
        return str(user_id)


def verifyUser(email, password):
    user = users.find_one({"email": email})
    if user and user["password"] == sha256(password):
        return str(user["_id"])
    else:
        return None


def getUser(id):
    return users.find_one({"_id": ObjectId(id)})

