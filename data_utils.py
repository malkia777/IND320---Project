from pymongo import MongoClient
uri = "mongodb://moi:v8E9aoZ6U5BkE3YI@ac-e3acgzz-shard-00-00.ylhzttp.mongodb.net:27017,ac-e3acgzz-shard-00-01.ylhzttp.mongodb.net:27017,ac-e3acgzz-shard-00-02.ylhzttp.mongodb.net:27017/?ssl=true&replicaSet=atlas-j59stf-shard-0&authSource=admin"
client = MongoClient(uri)
try:
    client.admin.command("ping")
    print("Connected successfully")
    client.close()

except Exception as e:
    raise Exception(
        "The following error occurred: ", e)