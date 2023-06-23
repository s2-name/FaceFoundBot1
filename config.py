
''' This is the configuration file of the FaceFoundBot bot '''

import os

# -------------TOKENs----------------
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")    # Telegram bot token (write https://t.me/BotFather)
# BOT_TOKEN = ""

QiWiTOKEN = os.getenv("QiWi_TOKEN")     # Token from the service WiQi P2P(
# QiWiTOKEN = ""

DB_LOGIN = ""           # MySQL user
DB_PASSWORD = ""        # user password
DB_SERVER = ""          # DataBase server (example, 10.10.53.13:3306)
# -------------TOKENs----------------

DEBUG_MODE = True       # If True, debugging information is output. False

# -------------OPTIONs----------------
COST_OF_VIP = 5                               # The cost of vip access (in RUB)
COUNT_OF_USERS_REQUESTS = 5                   # Number of requests from regular users per day

ADMINS_LIST = [713550923]                     # List of user ids with administrator status
ADMIN_USERNAME = "Stiv_208_name"                           # Username of the administrator to whom users with problems will write (without @)

TMP_IMG_DIR = "imgs"                            # Directory for temporary storage of images
SAVE_IMG_DIR = os.path.join("server", "media")  # Directory for permanent storage of images

IMG_COMPRESSION_RATIO = 0.9                     # Image compression ratio (0.1-1, where 0.1 is the minimum size, 1 is unchanged)
# -------------OPTIONs----------------