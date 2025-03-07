import os
import logging
from damgom_tokenizer import load_environment
from damgom_function import DamgomFunction

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.FileHandler('tokenizer.log'),
            logging.StreamHandler()
        ],
        encoding='utf-8'
    )

    # load environment variables
    load_environment()

    damgom = DamgomFunction()

    try:
        logging.info("Starting Damgom bot")
        damgom.bot.run(os.getenv("DISCORD_TOKEN_KEY"))
    except Exception as e:
        logging.error(f"Failed to start the bot: {e}")