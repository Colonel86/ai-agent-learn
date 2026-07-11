# load env variables 
from dotenv import load_dotenv
import os
   
# Load environment variables from .env file
load_dotenv()
   
# Verify the key loaded
print("API key loaded:", "Yes" if os.getenv('NVIDIA_API_KEY') else "No")