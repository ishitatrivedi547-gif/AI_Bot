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
from functools import wraps
from threading import Lock

import aiohttp
import jwt
import requests as req_lib
from flask import Flask, request, Response


#   CONFIG                                                     

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
BOT_NAME = os.environ.get("BOT_NAME", "AI Bot")
TEAMS_APP_ID = os.environ.get("APP_ID","ac487906-7f7a-47c5-b70b-4df3836c8542")
TEAMS_APP_PASSWORD = os.environ.get("APP_PASSWORD","8Iu8Q~wh6FcJZ1p-EO7q0Gsgr1pWQAO~DEEr5aEj")
TEAMS_TENANT_ID = os.environ.get("APP_TENANT_ID","0ac02500-802f-4a4c-bad2-7cd68064d701")
PORT = int(os.environ.get("PORT", 8000))

MAX_MESSAGE_LENGTH = 4000
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

MICROSOFT_BOT_FRAMEWORK_KEYS_URL = (
    "https://login.botframework.com/v1/.well-known/keys"
)

REQUIRED_VARS = {
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "APP_ID": TEAMS_APP_ID,
    "APP_PASSWORD": TEAMS_APP_PASSWORD,
    "APP_TENANT_ID": TEAMS_TENANT_ID,
}
missing = [k for k, v in REQUIRED_VARS.items() if not v]
if missing:
    print(f"❌ Missing required env vars: {', '.join(missing)}")
    raise SystemExit(1)



#   LOGGING                                                    

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
application = app  # for WSGI servers like gunicorn

#  TOKEN CACHES (thread-safe)                                 

class TokenCache:
    """Thread-safe token cache with automatic expiry."""

    def __init__(self, buffer_seconds: int = 300):
        self._token = None
        self._expires_at = None
        self._lock = Lock()
        self._buffer = timedelta(seconds=buffer_seconds)

    @property
    def is_valid(self) -> bool:
        with self._lock:
            return (
                self._token is not None
                and self._expires_at is not None
                and datetime.now(timezone.utc) < self._expires_at
            )

    def get(self) -> str | None:
        with self._lock:
            return self._token

    def set(self, token: str, expires_in: int):
        with self._lock:
            self._token = token
            self._expires_at = (
                datetime.now(timezone.utc)
                + timedelta(seconds=expires_in)
                - self._buffer
            )


class JWKSCache:
    """Thread-safe JWKS cache — refresh every 24 h or on cache miss."""

    def __init__(self):
        self._keys: dict = {}
        self._expires_at: datetime | None = None
        self._lock = Lock()

    @property
    def is_valid(self) -> bool:
        with self._lock:
            return (
                bool(self._keys)
                and self._expires_at is not None
                and datetime.now(timezone.utc) < self._expires_at
            )

    def get_key(self, kid: str):
        with self._lock:
            return self._keys.get(kid)

    def refresh(self, keys: list):
        with self._lock:
            self._keys = {k["kid"]: k for k in keys if "kid" in k}
            self._expires_at = datetime.now(timezone.utc) + timedelta(hours=24)


aad_token_cache = TokenCache(buffer_seconds=300)
jwks_cache = JWKSCache()


#   SHARED ASYNC HTTP SESSION                                  

_session: aiohttp.ClientSession | None = None


async def get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            connector=aiohttp.TCPConnector(limit=20),
        )
    return _session


def _cleanup_session():
    global _session
    if _session and not _session.closed:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(_session.close())
        loop.close()


import atexit
atexit.register(_cleanup_session)



#   ASYNC HELPER (works inside & outside running loops)        

def run_async(coro):
    """Run a coroutine safely whether or not an event loop is active."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor() as pool:
        return pool.submit(asyncio.run, coro).result()

#   JWT / TOKEN VERIFICATION                                   

def _fetch_jwks() -> list | None:
    """Fetch Microsoft's public signing keys (cached 24 h)."""
    try:
        resp = req_lib.get(MICROSOFT_BOT_FRAMEWORK_KEYS_URL, timeout=10)
        resp.raise_for_status()
        keys = resp.json().get("keys", [])
        jwks_cache.refresh(keys)
        logger.info("JWKS refreshed (%d keys)", len(keys))
        return keys
    except Exception as e:
        logger.error("Failed to fetch JWKS: %s", e)
        return None


def verify_token(auth_header: str) -> bool:
    """Verify the incoming request is from Microsoft Bot Framework."""
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("Missing or malformed Authorization header")
        return False

    token = auth_header.split(" ", 1)[1]

    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            logger.warning("Token header missing 'kid'")
            return False

        # Try cached keys first, then refresh on miss
        key_data = jwks_cache.get_key(kid)
        if key_data is None:
            keys = _fetch_jwks()
            if not keys:
                return False
            key_data = jwks_cache.get_key(kid)
        if key_data is None:
            logger.warning("No matching signing key found (kid=%s)", kid)
            return False

        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
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
    except jwt.ImmatureSignatureError:
        logger.warning("Token not yet valid (nbf)")
    except jwt.InvalidSignatureError:
        logger.warning("Invalid token signature")
    except Exception as e:
        logger.warning("Token verification failed: %s", e)

    return False

#   AAD TOKEN (for sending replies to Teams)                   

async def get_aad_token() -> str:
    if aad_token_cache.is_valid:
        return aad_token_cache.get()

    url = (
        f"https://login.microsoftonline.com/{TEAMS_TENANT_ID}"
        "/oauth2/v2.0/token"
    )
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
        logger.error("Failed to obtain AAD token: %s", data)
        raise RuntimeError("AAD token request failed")

    expires_in = data.get("expires_in", 3600)
    aad_token_cache.set(token, expires_in)
    logger.info("AAD token refreshed (expires in %ds)", expires_in)
    return token

#  OPENAI — generate response                                 

SYSTEM_PROMPT = (
    "You are a helpful, friendly AI assistant integrated into "
    "Microsoft Teams. Give clear, concise answers. "
    "If you don't know something, say so honestly."
)

ERROR_RESPONSES = {
    "rate_limit": "I'm getting too many requests right now — please wait a moment and try again.",
    "auth": "There's an authentication problem with the AI service. Please notify the admin.",
    "connection": "I'm having trouble reaching the AI service. Please try again shortly.",
    "empty": "I wasn't able to generate a response. Could you rephrase your question?",
    "generic": "Something went wrong while processing your request. Please try again.",
}


async def generate_ai_response(user_message: str) -> str:
    """Send a message to OpenAI and return the assistant reply."""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
    }

    try:
        session = await get_session()
        async with session.post(
            OPENAI_URL, json=payload, headers=headers
        ) as resp:
            data = await resp.json()

            if resp.status == 429:
                logger.warning("OpenAI rate limit hit")
                return ERROR_RESPONSES["rate_limit"]

            if resp.status == 401:
                logger.error("OpenAI auth error: %s", data)
                return ERROR_RESPONSES["auth"]

            if resp.status != 200:
                logger.error("OpenAI error [%d]: %s", resp.status, data)
                return ERROR_RESPONSES["generic"]

            choices = data.get("choices")
            if (
                not choices
                or not choices[0].get("message", {}).get("content")
            ):
                logger.error("OpenAI returned empty choices: %s", data)
                return ERROR_RESPONSES["empty"]

            return choices[0]["message"]["content"]

    except aiohttp.ClientError as e:
        logger.error("OpenAI connection error: %s", e)
        return ERROR_RESPONSES["connection"]
    except Exception as e:
        logger.error("Unexpected OpenAI error: %s", e)
        return ERROR_RESPONSES["generic"]

#   SEND REPLY TO TEAMS                                        

async def send_reply(
    service_url: str, conversation_id: str, reply: dict
) -> bool:
    token = await get_aad_token()
    url = f"{service_url}v3/conversations/{conversation_id}/activities"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        session = await get_session()
        async with session.post(url, json=reply, headers=headers) as resp:
            if resp.status in (200, 201):
                return True
            error_text = await resp.text()
            logger.error(
                "Failed to send reply [%d]: %s", resp.status, error_text
            )
            return False
    except aiohttp.ClientError as e:
        logger.error("Connection error sending reply: %s", e)
        return False
    except Exception as e:
        logger.error("Unexpected error sending reply: %s", e)
        return False

#   BUILD REPLY ACTIVITY                                       

def build_reply(activity: dict, text: str) -> dict:
    return {
        "type": "message",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "from": {"id": TEAMS_APP_ID, "name": BOT_NAME},
        "conversation": activity.get("conversation"),
        "recipient": activity.get("from"),
        "replyToId": activity.get("id"),
        "text": text,
    }


def _is_bot_member(member: dict) -> bool:
    """Return True if the member is the bot itself."""
    member_id = member.get("id", "")
    # Teams bot IDs can be "28:<appId>" or just the appId
    return (
        TEAMS_APP_ID in member_id
        or member_id == TEAMS_APP_ID
        or member.get("name") == BOT_NAME
    )

#  MAIN ROUTE  /api/messages                                  

@app.route("/api/messages", methods=["POST"])
def messages():
    try:
        # ── 1. Auth ──
        auth_header = request.headers.get("Authorization")
        if not verify_token(auth_header):
            return Response(status=401)

        # ── 2. Parse ──
        data = request.get_json(silent=True)
        if not data:
            return Response(status=400)

        activity_type = data.get("type", "")

        # ── 3. Handle ──
        if activity_type == "message":
            _handle_message(data)

        elif activity_type == "conversationUpdate":
            _handle_conversation_update(data)

        else:
            logger.debug("Ignoring activity type: %s", activity_type)

        return Response("{}", status=200)

    except Exception as e:
        logger.error("Handler error: %s", e, exc_info=True)
        return Response("{}", status=200)


def _handle_message(data: dict):
    """Process an incoming message, generate AI reply, send it back."""
    user_message = (data.get("text") or "").strip()[:MAX_MESSAGE_LENGTH]
    from_name = data.get("from", {}).get("name", "User")
    service_url = data.get("serviceUrl")
    conv_id = data.get("conversation", {}).get("id")

    if not user_message:
        logger.info("Empty message from %s — skipped", from_name)
        return

    if not service_url or not conv_id:
        logger.warning("Missing serviceUrl or conversation id")
        return

    logger.info("📩 [%s] %s", from_name, user_message[:120])

    async def process():
        ai_reply = await generate_ai_response(user_message)
        reply = build_reply(data, ai_reply)
        ok = await send_reply(service_url, conv_id, reply)
        status = "✅" if ok else "❌"
        logger.info("%s Reply to %s (%d chars)", status, from_name, len(ai_reply))

    run_async(process())


def _handle_conversation_update(data: dict):
    """Send a welcome message when the bot is added to a conversation."""
    members_added = data.get("membersAdded", [])
    service_url = data.get("serviceUrl")
    conv_id = data.get("conversation", {}).get("id")

    if not service_url or not conv_id:
        return

    # Build welcome texts
    welcome_texts = [
        f"👋 Hello! I'm **{BOT_NAME}** — your AI assistant.",
        "Ask me anything and I'll do my best to help!",
    ]
    welcome_message = "\n".join(welcome_texts)

    async def send_welcome():
        for member in members_added:
            if _is_bot_member(member):
                continue  # skip the bot itself
            reply = build_reply(data, welcome_message)
            await send_reply(service_url, conv_id, reply)
            logger.info("👋 Sent welcome to %s", member.get("name", "?"))

    run_async(send_welcome())

#   HEALTH & HOME                                              

@app.route("/health")
def health():
    return {
        "status": "ok",
        "bot": BOT_NAME,
        "model": OPENAI_MODEL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.route("/")
def home():
    return f"🤖 {BOT_NAME} is running 🚀"

 #ENTRY POINT                                                

if __name__ == "__main__":
    logger.info("Starting %s on port %d …", BOT_NAME, PORT)
    app.run(host="0.0.0.0", port=PORT)
