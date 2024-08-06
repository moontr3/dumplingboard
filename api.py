from copy import deepcopy
import random
from typing import *

import discord
from config import *
import json
import os
import time
from log import *


# guild-related classes

class Post:
    def __init__(self, msg_id:int, number:int, post_id:"int | None"=None, reactions:int=1):
        '''
        Represents a guild.
        '''
        self.number: int = number
        self.id: int = msg_id
        self.post_id: "int | None" = post_id
        self.reactions: int = reactions

    
    def to_dict(self) -> dict:
        '''
        Converts the class to a dictionary to store in the file.
        '''
        return {
            "number": self.number,
            "id": self.id,
            "post_id": self.post_id,
            "reactions": self.reactions
        }
    

class Guild:
    def __init__(self, id:int, data:dict={}):
        '''
        Represents a guild.
        '''
        self.id: int = id
        self.from_dict(data)


    def get_post(self, id:int) -> "Post | None":
        '''
        Checking if post exists and returning it.
        '''
        for i in self.sent_posts:
            if i.id == id:
                return i


    def from_dict(self, data:dict={}):
        '''
        Replaces current guild data with data from a dict.
        '''
        self.creation_time: int = data.get('creation_time', time.time())
        self.db_channel: int = data.get('db_channel', None) # dumplingboard channel
        self.sent_posts: List[Post] = [
            Post(i['id'], i['number'], i['post_id'], i['reactions'])\
            for i in data.get('posts', [])
        ]
        self.reactions: int = data.get('reactions', 3)

    
    def to_dict(self) -> dict:
        '''
        Converts the class to a dictionary to store in the file.
        '''
        return {
            "creation_time": self.creation_time,
            "db_channel": self.db_channel,
            "posts": [i.to_dict() for i in self.sent_posts],
            "reactions": self.reactions
        }
    

# manager

class Manager:
    def __init__(self):
        '''
        API and backend manager.
        '''
        self.reload()


    def new(self):
        '''
        Rewrites the old database with the new one.
        '''
        self.guilds: Dict[int, Guild] = {}
        
        self.commit()


    def panic(self):
        '''
        Creates a duplicate of the database and creates a new one.
        '''
        log('Panic!', 'api', WARNING)

        # copying file
        if os.path.exists(DATA_FILE):
            os.rename(DATA_FILE, DATA_FILE+'.bak')
            log(f'Cloned data file to {DATA_FILE}.bak', 'api')

        # creating a new one
        self.new()


    def reload(self):
        '''
        Reloads bot data.
        '''
        # data
        try:
            with open(DATA_FILE, encoding='utf-8') as f:
                data = json.load(f)
            log('Reloaded data', 'api')

        except Exception as e:
            log(f'Error while loading data: {e}', 'api', level=ERROR)
            self.panic()
            return

        self.guilds = {int(id): Guild(int(id), data) for id, data in data['guilds'].items()}

        # saving
        self.commit()


    def commit(self):
        '''
        Saves data to the file.
        '''
        data = {
            'guilds': {}
        }

        # guilds
        for i in self.guilds:
            data['guilds'][i] = self.guilds[i].to_dict()

        # saving
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)


    def check_guild(self, id:int):
        '''
        Checks if guild exists in database. If not, creates one.
        '''
        if id in self.guilds:
            return
        
        self.guilds[id] = Guild(id)


    def send_post(self, guild_id:int, message_id:int) -> Post:
        '''
        Sets the guild's channel.
        '''
        self.check_guild(guild_id)

        guild = self.guilds[guild_id]
        post = Post(message_id, len(guild.sent_posts)+1)
        self.guilds[guild_id].sent_posts.append(post)

        self.commit()

        return post


    def set_post_id(self, guild_id:int, index:int, id:int):
        '''
        Sets the posts' post ID.
        '''
        self.check_guild(guild_id)

        self.guilds[guild_id].sent_posts[index-1].post_id = id

        self.commit()


    def set_post_reactions(self, guild_id:int, index:int, amount:int):
        '''
        Sets the posts' post ID.
        '''
        self.check_guild(guild_id)

        self.guilds[guild_id].sent_posts[index-1].reactions = amount

        self.commit()


    def set_channel(self, guild_id:int, channel_id:int):
        '''
        Sets the guild's channel.
        '''
        self.check_guild(guild_id)

        self.guilds[guild_id].db_channel = channel_id

        self.commit()


    def set_reactions(self, guild_id:int, amount:int):
        '''
        Sets the guild's reaction amount.
        '''
        self.check_guild(guild_id)

        self.guilds[guild_id].reactions = amount

        self.commit()


    def remove_channel(self, guild_id:int):
        '''
        Removes the guild's channel.
        '''
        self.check_guild(guild_id)

        self.guilds[guild_id].db_channel = None

        self.commit()