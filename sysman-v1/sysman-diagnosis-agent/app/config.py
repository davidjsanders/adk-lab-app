from dotenv import load_dotenv
from app.classes.settings import Settings

# Populate environment
load_dotenv(override=True)

settings = Settings()
