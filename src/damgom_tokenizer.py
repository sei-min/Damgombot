import os
import logging
from dotenv import load_dotenv

# load discord token
def load_environment():
    load_dotenv('../.env')
    if not os.getenv("DISCORD_TOKEN_KEY"):
        logging.error("Discord token not found")
        raise EnvironmentError("Discord token not found in .env file")
