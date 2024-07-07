# quart & compress for web stuff
from quart import Quart, flash, request, redirect, render_template, jsonify, session
from quart_compress import Compress

# uvloop for speed
import uvloop

# json for storage
import json

# os for bot token
import os

# asyncio for async
import asyncio

# hikari for api
import hikari

# starts hikari
rest_app = hikari.RESTApp()

# may remove this
"""class User:
    def __init__(self, name):
        self.name = name
        self.connected = []
    
    def connect(self, users, type):
        self.connected.extend([{user: type} for user in users])
    
    def __str__(self):
        return "\n".join([
            f"name: {self.name}\n"
            f"neighbors: {[[(u.name, t) for u, t in user.items()][0]
            for user in self.connected]}"
        ])"""

# runs uvloop, initiates quart & compresses quart
uvloop.install()
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
app = Quart(__name__)
Compress(app)

# specifies avatar url for failed users
default_avatar_url = "https://cdn.glitch.global/269cebce-0e77-45c8-8657-9e20c05be5bd/failed.webp?size=64"

# home
@app.route('/')
async def index():
    # renders website
    return await render_template("index.html")

# grabs tree
@app.route("/tree", methods=["GET"])
async def gum_tree():
    # opens tree data
    with open("trees/t0001.json", "r") as f:
        # returns tree data
        return jsonify(json.load(f))

# grabs user
@app.route("/user", methods=["POST"])
async def user_data(server=False, id=None):
    # if client request:
    if not server:
        req_data = await request.get_json()
        id = int(req_data["id"])
    
    # > hikari docs home rest-only app example 
    #   has connection defined outside of async function
    # > "oh cool lemme copy"
    # > works in older version of hikari
    # > "lemme update hikari"
    # > latest docs has same definition scheme
    # > no longer works in latest version
    # > have to move connection definition into here for
    #   some pecking reason
    # > this took four hours
    # why? has i ever?
    rest_app = hikari.RESTApp()
    
    # starts connection
    await rest_app.start()
    # with rest client instance
    async with rest_app.acquire(os.environ['TOKEN'], "Bot") as client:
        # fetches user object
        try:
            # if valid id
            user = await client.fetch_user(id)
        except (hikari.errors.NotFoundError, hikari.errors.BadRequestError):
            # notifies of failure & sets default user info
            success = False
            print(f"FAILED: {id}")
            avatar = default_avatar_url
            username = f"error [ID: {id}]"
        else:
            success = True
            # gets avatar url
            avatar = str(user.display_avatar_url)
            # if avatar isn't default
            if "embed" not in avatar.split("/avatars/")[0]:
              # convert to webp (default ones don't support a webp request)
              avatar = avatar.replace(".png", ".webp")
            # other user info
            username = user.username
            # prints username for the sake of logging
            print(user.username)
    # closes connection
    await rest_app.close()
    print(avatar)
    return {
        str(id): {
            "username": username,
            # sets img size
            "avatar": avatar.split("?")[0] + "?size=64",
            "success": success
        }
    }

# updates user data via id
@app.route("/update_user", methods=["POST"])
# server boolean 2: electric boogaloo
async def update_user(server=False, id=None):
    # if client request:
    if not server:
        req_data = await request.get_json()
        id = req_data["id"]
    # grabs tree data
    print("check")
    with open("trees/t0001.json", "r") as oldtree, open("trees/newt0001.json", "w") as newtree:
        tree_data = json.loads(oldtree.read())
        user_info = tree_data["user_info"]
        old_data = user_info[id]
        # grabs updated user data
        new_data = await user_data(True, id)
        # if user id is no longer valid for whatever reason
        if not new_data[id]["success"]:
            # halt update & preserve old data
            print("update halted; id no longer valid")
            return old_data
        # writes & logs the update
        user_info.update(new_data)
        newtree.write(json.dumps(tree_data, indent=4))
        os.rename("trees/newt0001.json", "trees/t0001.json")
        print(f"updates: {dict(set(new_data[id].items()) - set(old_data.items()))}")
    # returns current data
    return new_data

# basically runs update_user_data on every id in tree
@app.route("/update_tree", methods=["POST"])
async def update_tree():
    # opens tree data & loads ids
    with open("trees/t0001.json", "r") as tree:
        ids = json.load(tree).keys()["user_info"]
    # for id in ids
    for str_id in ids:
        # updates & logs
        print(f"\nupdating user id {str_id}")
        await update_user(True, str_id)
        # WHY DO I HAVE TO WAIT 0.5 SECONDS TO PREVENT RATELIMITING I DON'T GET IT
        # LEGIT 0.05 SHOULD BE MORE THAN ENOUGH BUT NO
        # CMON MAN
        
        # looking at this a year later, perhaps i know why
        # TODO: check if this is actually halting the loop for 0.5s
        await asyncio.sleep(0.5)
    # returns tree data
    return await gum_tree()

# unnecessary here but good practice ig
if __name__ == "__main__":
    # runs app
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=True
    )
