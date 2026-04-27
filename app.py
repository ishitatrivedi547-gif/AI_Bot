"""Simple Teams Bot - Fixed Response.

from flask import Flask, request, Response, make_response
import json
import logging
import asyncio
from teams_utils import send_reply_to_teams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
application = app

BOT_ID = "8ccf0c00-61ef-4fcc-86af-dcf60dec0d5a"


@app.route("/api/messages", methods=["POST"])
def messages():
    try:
        data = request.get_json()
        
        if data.get("type") == "message":
            msg_id = data.get("id")
            conv_id = data.get("conversation", {}).get("id")
            service_url = data.get("serviceUrl")
            user_text = data.get("text", "").lower()
            user_name = data.get("from", {}).get("name", "User")

            # 🔹 Dynamic reply logic
            if "hello" in user_text:
                bot_reply = f"Hi {user_name}! 👋"
            elif "help" in user_text:
                bot_reply = "Sure! Tell me what you need help with."
            else:
                bot_reply = f"You said: {user_text}"

            reply = {
                "type": "message",
                "text": bot_reply
            }

            # 🔹 Call async function properly
            asyncio.run(send_reply_to_teams(
                service_url,
                conv_id,
                msg_id,
                reply
            ))

            
        return Response("{}", status=200)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return Response("{}", status=200)


@app.route("/")
def home():
    return "Bot running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)"""

"""Teams Bot with Bot Connector API integration."""
 
from flask import Flask, request, Response
import json
import logging
import os
import asyncio
import aiohttp
from datetime import datetime, timedelta
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
app = Flask(__name__)
application = app
 
# Bot Configuration
BOT_ID = "ac487906-7f7a-47c5-b70b-4df3836c8542"
BOT_NAME = "AI Bot"
 
# Azure AD Configuration (load from environment variables)
TEAMS_APP_ID = os.environ.get("APP_ID", "")
TEAMS_APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
TEAMS_TENANT_ID = os.environ.get("App_TENANT_ID", "")
 
# Token cache (simple in-memory cache)
_token_cache = {"token": None, "expires_at": None}
 
def _build_reply(activity: dict, text: str) -> dict:

    return {

        "type": "message",

        "timestamp": datetime.utcnow().isoformat(),

        "from": activity.get("recipient") or {

            "id": TEAMS_APP_ID,

            "name": BOT_NAME

        },

        "conversation": activity.get("conversation"),

        "recipient": activity.get("from"),

        "replyToId": activity.get("id"),

        "text": text,

    }
 
async def _get_aad_token() -> str:
    """
    Acquire AAD Bearer token for Bot Connector API using client credentials flow.
    """
    # Check if token is still valid
    if _token_cache["token"] and _token_cache["expires_at"]:
        if datetime.utcnow() < _token_cache["expires_at"]:
            return _token_cache["token"]
    # Get new token
    token_url = f"https://login.microsoftonline.com/{TEAMS_TENANT_ID}/oauth2/v2.0/token"
    payload = {
        "client_id": TEAMS_APP_ID,
        "client_secret": TEAMS_APP_PASSWORD,
        "scope": "https://api.botframework.com/.default",
        "grant_type": "client_credentials",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=payload) as resp:
                if resp.status != 200:
                    logger.error(f"Failed to get token: {resp.status}")
                    return None
                data = await resp.json()
                token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)
                # Cache token (expires in 5 minutes before actual expiry)
                _token_cache["token"] = token
                _token_cache["expires_at"] = datetime.utcnow() + timedelta(seconds=expires_in - 300)
                logger.info("AAD token acquired")
                return token
    except Exception as e:
        logger.error(f"Error acquiring AAD token: {e}")
        return None
    
async def send_reply_to_teams(service_url, conversation_id, reply):

    url = f"{service_url}v3/conversations/{conversation_id}/activities"
 
    token = await _get_aad_token()
 
    headers = {

        "Authorization": f"Bearer {token}",

        "Content-Type": "application/json"

    }
 
    async with aiohttp.ClientSession() as session:

        async with session.post(url, json=reply, headers=headers) as resp:

            text = await resp.text()

            if resp.status not in [200, 201]:

                logger.error(f"Failed: {resp.status} - {text}")

                return False
 
    return True
 
 
 
"""async def send_reply_to_teams(service_url: str, conversation_id: str, activity_id: str, reply_text: str) -> bool:
    """
    #Send reply back to Teams via Bot Connector API with AAD Bearer token.
    """
    url = f"{service_url}v3/conversations/{conversation_id}/activities"
    reply_data = {
        "type": "message",
        "text": reply_text
    }
    try:
        token = await _get_aad_token()
        if not token:
            logger.error("Failed to acquire token, cannot send reply")
            return False
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=reply_data, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status not in [200, 201]:
                    error_text = await resp.text()
                    logger.error(f"Failed to send reply: {resp.status} - {error_text}")
                    return False
                logger.info(f"Reply sent to Teams successfully (status: {resp.status})")
                return True
    except Exception as e:
        logger.error(f"Error sending reply to Teams: {e}")
        return False"""
 
 
def run_async_task(coro):
    """Helper to run async code from sync Flask route."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
 
 
@app.route("/api/messages", methods=["POST"])
def messages():
    try:
        data = request.get_json()
        if data.get("type") == "message":
            # Extract required fields
            msg_id = data.get("id")
            service_url = data.get("serviceUrl")
            conv_id = data.get("conversation", {}).get("id")
            from_id = data.get("from", {}).get("id")
            from_name = data.get("from", {}).get("name", "User")
            user_message = data.get("text", "")
            logger.info(f"Message from {from_name}: {user_message}")
            if not all([msg_id, service_url, conv_id]):
                logger.error("Missing required fields in Teams activity")
                return Response("{}", status=200)
            # Prepare reply
            reply_text = f"Hello {from_name}!. How can I help you today?"
            # Send reply via Bot Connector API
            success = run_async_task(send_reply_to_teams(service_url, conv_id, msg_id, reply_text))
            if success:
                logger.info("Message processed and reply sent")
            else:
                logger.warning("Failed to send reply")
            return Response("{}", status=200)
        return Response("{}", status=200)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return Response("{}", status=200)
 
 
@app.route("/")
def home():
    return "Bot running"
 
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)