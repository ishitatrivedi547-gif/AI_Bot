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

 
"""from flask import Flask, request, Response
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

# Azure AD Configuration
TEAMS_APP_ID = os.environ.get("APP_ID", "")
TEAMS_APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
TEAMS_TENANT_ID = os.environ.get("App_TENANT_ID", "")

# Token cache
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
    if _token_cache["token"] and _token_cache["expires_at"]:
        if datetime.utcnow() < _token_cache["expires_at"]:
            return _token_cache["token"]

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

    if not token:
        logger.error("No token available")
        return False

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


def run_async_task(coro):
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
            msg_id = data.get("id")
            service_url = data.get("serviceUrl")
            conv_id = data.get("conversation", {}).get("id")
            from_name = data.get("from", {}).get("name", "User")
            user_message = data.get("text", "")

            logger.info(f"Message from {from_name}: {user_message}")

            if not all([msg_id, service_url, conv_id]):
                logger.error("Missing required fields")
                return Response("{}", status=200)

            reply_text = f"Hello {from_name}! How can I help you today?"

            reply = _build_reply(data, reply_text)

            success = run_async_task(
                send_reply_to_teams(service_url, conv_id, reply)
            )

            if success:
                logger.info("Reply sent")
            else:
                logger.warning("Reply failed")

        return Response("{}", status=200)

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return Response("{}", status=200)


@app.route("/")
def home():
    return "Bot running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)"""


import logging
import os
import asyncio
import concurrent.futures
from datetime import datetime, timedelta, timezone

import aiohttp
import jwt
import requests as req_lib
from flask import Flask, request, Response

# ====== CONFIG ======
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
BOT_NAME = "AI Bot"
TEAMS_APP_ID = os.environ.get("APP_ID")
TEAMS_APP_PASSWORD = os.environ.get("APP_PASSWORD")
TEAMS_TENANT_ID = os.environ.get("APP_TENANT_ID")

# Validate required env vars at startup
REQUIRED_VARS = {
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "APP_ID": TEAMS_APP_ID,
    "APP_PASSWORD": TEAMS_APP_PASSWORD,
    "APP_TENANT_ID": TEAMS_TENANT_ID,
}
missing = [k for k, v in REQUIRED_VARS.items() if not v]
if missing:
    raise RuntimeError(f"Missing required environment variables: {missing}")

MAX_MESSAGE_LENGTH = 4000
MICROSOFT_BOT_FRAMEWORK_KEYS_URL = "https://login.botframework.com/v1/.well-known/keys"

# ====== LOGGING ======
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
application = app

# ====== TOKEN CACHE ======
_token_cache = {"token": None, "expires_at": None}

# ====== SHARED HTTP SESSION ======
_session = None


async def get_session():
    """Reuse a single aiohttp session for connection pooling."""
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
    return _session


def cleanup_session():
    """Close the shared session on shutdown."""
    global _session
    if _session and not _session.closed:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(_session.close())
        loop.close()


import atexit
atexit.register(cleanup_session)


# ====== ASYNC RUNNER ======
def run_async(coro):
    """Safely run async code whether or not a loop is already running."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)


# ====== TOKEN VERIFICATION ======
def verify_token(auth_header: str) -> bool:
    """Verify that the incoming request is from Microsoft Bot Framework."""
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("Missing or malformed Authorization header")
        return False

    token = auth_header.split(" ")[1]

    try:
        # Fetch Microsoft's public signing keys (cache this in production)
        jwks = req_lib.get(MICROSOFT_BOT_FRAMEWORK_KEYS_URL, timeout=10).json()
        unverified_header = jwt.get_unverified_header(token)

        for key in jwks.get("keys", []):
            if key.get("kid") == unverified_header.get("kid"):
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                jwt.decode(
                    token,
                    public_key,
                    algorithms=["RS256"],
                    audience=TEAMS_APP_ID,
                    issuer="https://api.botframework.com",
                )
                return True

    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
    except jwt.InvalidAudienceError:
        logger.warning("Invalid token audience")
    except jwt.InvalidIssuerError:
        logger.warning("Invalid token issuer")
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")

    return False


# ====== BUILD REPLY ======
def build_reply(activity: dict, text: str) -> dict:
    return {
        "type": "message",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "from": {
            "id": TEAMS_APP_ID,
            "name": BOT_NAME,
        },
        "conversation": activity.get("conversation"),
        "recipient": activity.get("from"),
        "replyToId": activity.get("id"),
        "text": text,
    }


# ====== GET AAD TOKEN ======
async def get_aad_token() -> str:
    if _token_cache["token"] and datetime.now(timezone.utc) < _token_cache["expires_at"]:
        return _token_cache["token"]

    url = f"https://login.microsoftonline.com/{TEAMS_TENANT_ID}/oauth2/v2.0/token"
    payload = {
        "client_id": TEAMS_APP_ID,
        "client_secret": TEAMS_APP_PASSWORD,
        "scope": "https://api.botframework.com/.default",
        "grant_type": "client_credentials",
    }

    session = await get_session()
    async with session.post(url, data=payload) as resp:
        data = await resp.json()

        token = data.get("access_token")
        if not token:
            logger.error(f"Failed to get AAD token: {data}")
            raise RuntimeError("Failed to obtain AAD token")

        expires_in = data.get("expires_in", 3600)
        _token_cache["token"] = token
        _token_cache["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 300)

        logger.info("AAD token refreshed successfully")
        return token


# ====== CALL OPENAI ======
async def generate_ai_response(user_message: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4.1-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant for Microsoft Teams."},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    try:
        session = await get_session()
        async with session.post(url, json=payload, headers=headers) as resp:
            data = await resp.json()

            if resp.status != 200:
                logger.error(f"OpenAI API error [{resp.status}]: {data}")
                return "Sorry, I encountered an error while processing your request. Please try again later."

            choices = data.get("choices")
            if not choices or not choices[0].get("message", {}).get("content"):
                logger.error(f"OpenAI returned no choices: {data}")
                return "Sorry, I couldn't generate a response. Please try again."

            return choices[0]["message"]["content"]

    except aiohttp.ClientError as e:
        logger.error(f"OpenAI connection error: {e}")
        return "Sorry, I'm having trouble connecting to the AI service. Please try again later."
    except Exception as e:
        logger.error(f"Unexpected OpenAI error: {e}")
        return "Sorry, an unexpected error occurred. Please try again later."


# ====== SEND TO TEAMS ======
async def send_reply(service_url: str, conversation_id: str, reply: dict) -> bool:
    token = await get_aad_token()
    url = f"{service_url}v3/conversations/{conversation_id}/activities"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        session = await get_session()
        async with session.post(url, json=reply, headers=headers) as resp:
            if resp.status not in [200, 201]:
                error_text = await resp.text()
                logger.error(f"Failed to send reply [{resp.status}]: {error_text}")
                return False

            return True

    except aiohttp.ClientError as e:
        logger.error(f"Connection error sending reply: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending reply: {e}")
        return False


# ====== MAIN ROUTE ======
@app.route("/api/messages", methods=["POST"])
def messages():
    try:
        # 1) Verify token
        auth_header = request.headers.get("Authorization")
        if not verify_token(auth_header):
            return Response(status=401)

        # 2) Parse payload
        data = request.get_json()
        if not data:
            return Response(status=400)

        activity_type = data.get("type")

        # 3) Handle message activities only
        if activity_type == "message":
            user_message = data.get("text", "")[:MAX_MESSAGE_LENGTH]
            from_name = data.get("from", {}).get("name", "User")
            service_url = data.get("serviceUrl")
            conv_id = data.get("conversation", {}).get("id")

            if not user_message.strip():
                logger.info(f"Empty message from {from_name}")
                return Response("{}", status=200)

            if not service_url or not conv_id:
                logger.warning("Missing serviceUrl or conversation id")
                return Response("{}", status=400)

            logger.info(f"Message from {from_name}: {user_message[:100]}...")

            async def process():
                ai_reply = await generate_ai_response(user_message)
                reply = build_reply(data, ai_reply)
                success = await send_reply(service_url, conv_id, reply)
                if not success:
                    logger.error(f"Failed to deliver reply to {from_name}")

            run_async(process())

        elif activity_type == "conversationUpdate":
            members_added = data.get("membersAdded", [])
            service_url = data.get("serviceUrl")
            conv_id = data.get("conversation", {}).get("id")

            async def send_welcome():
                for member in members_added:
                    member_id = member.get("id", "")
                    if TEAMS_APP_ID and TEAMS_APP_ID not in member_id:
                        welcome = build_reply(data, f"Hello! I'm {BOT_NAME}. Ask me anything!")
                        await send_reply(service_url, conv_id, welcome)

            if service_url and conv_id:
                run_async(send_welcome())

        else:
            # conversationUpdate, typing, invoke, etc. — acknowledge silently
            logger.info(f"Ignoring activity type: {activity_type}")

        return Response("{}", status=200)

    except Exception as e:
        logger.error(f"Handler error: {e}", exc_info=True)
        return Response("{}", status=200)


# ====== HEALTH CHECK ======
@app.route("/health")
def health():
    return {
        "status": "ok",
        "bot": BOT_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.route("/")
def home():
    return "Bot is running 🚀"


# ====== ENTRY POINT ======
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)