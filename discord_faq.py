"""
Discord bot that responds to user messages using a FAQ chatbot system.

This bot listens for messages on a Discord server and replies with relevant information based on 
predefined questions and answers. The bot utilizes a FAQ system to understand user input and generate 
appropriate responses.

Author: Mohammad Moaddeli
Date: 2024-10-16
Sources:
- Discord.py documentation: https://discordpy.readthedocs.io/en/stable/
- FAQ system from faq_skeleton module

Note:
This bot uses `faq_skeleton`, which contains the functions `understand()` and `response_generate()` 
to process user input and generate responses.
"""

import discord
from faq_skeleton import *

class MyClient(discord.Client):
    """
    A custom Discord client that listens for messages and responds based on a FAQ system.

    The bot interacts with a user by listening for incoming messages in any channel and processing 
    those messages to generate a relevant response using predefined questions and answers from the 
    FAQ system.

    Methods:
    - __init__(): Initializes the bot with the required intents.
    - on_ready(): Called when the bot has successfully connected to Discord.
    - on_message(message): Called when a message is sent in a Discord channel the bot is in.
    """
    
    def __init__(self):
        """
        Initializes the Discord bot with default message content intents.
        
        The bot is set up to listen for message content, which is required for reading user input 
        and generating responses. This is done by enabling the `message_content` intent.
        """
        intents = discord.Intents.default()
        intents.message_content = True  # Required to listen for message content
        super().__init__(intents=intents)

    async def on_ready(self):
        """
        Event handler that is called when the bot has successfully logged in and is ready.
        
        This method will be called once the bot connects to Discord. It logs a message showing 
        the bot's username to confirm the bot is running.
        """
        print('Logged on as', self.user)

    async def on_message(self, message):
        """
        Event handler that is triggered when a message is sent in any channel the bot is in.
        
        If the message is not from the bot itself, the bot will process the message, generate 
        a response, and send the response back to the channel.

        Parameters:
        message (discord.Message): The message object that contains information about the 
                                   content, author, and channel of the message.
        
        Behavior:
        - Ignores messages sent by the bot itself.
        - Uses the `understand()` function to determine the intent based on the message content.
        - Uses the `response_generate()` function to create a response based on the intent.
        - Sends the generated response back to the channel where the message was received.
        """
        # don't respond to ourselves
        if message.author == self.user:
            return
        
        # Get the user's message and generate the response using FAQ system functions
        utterance = message.content
        intent, responseLink = understand(utterance)
        response = response_generate(intent, responseLink)

        # Send the response back to the Discord channel
        await message.channel.send(response)

## Set up and log in
client = MyClient()

with open("bot_token.txt") as file:
    """
    Reads the bot's authentication token from a file and starts the bot.
    
    The bot token is loaded from `bot_token.txt`, which should contain the bot's token provided by 
    Discord. This token is used to authenticate and connect the bot to the Discord API.
    
    The `client.run(token)` call starts the bot and connects it to the Discord server.
    """
    token = file.read()

client.run(token)
