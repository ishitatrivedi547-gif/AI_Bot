# Teams LangChain Chatbot

A Microsoft Teams chatbot powered by **Python**, **LangChain**, and **OpenAI** that provides intelligent conversational responses with memory.

## Project Structure

```
teams-langchain-bot/
├── src/
│   ├── __init__.py
│   ├── config.py                # Environment configuration loader
│   ├── langchain_service.py     # LangChain + OpenAI + BufferMemory
│   ├── bot.py                   # Teams bot handler (ActivityHandler)
│   └── app.py                   # aiohttp web server entry point
├── appPackage/
│   ├── manifest.json            # Teams app manifest (for sideloading)
│   ├── color.png                # App icon (192x192)
│   └── outline.png              # App outline icon (32x32)
├── .env.example                 # Environment variable template
├── requirements.txt             # Python dependencies
├── generate_icons.py            # Helper to generate manifest icons
└── README.md
```

## How It Works

```
User sends message in Teams
    → Teams sends POST to /api/messages
    → src/app.py receives HTTP request
    → src/bot.py processes the activity
    → src/langchain_service.py calls OpenAI via LangChain
        → ConversationBufferMemory keeps chat history per conversation
    → Response sent back to Teams
```

## Prerequisites

1. **Python 3.9+** — [Download](https://www.python.org/downloads/)
2. **OpenAI API key** — [Get one here](https://platform.openai.com/api-keys)
3. **Azure Bot registration** (bot ID + password) — see [Step 1](#step-1-register-a-bot-in-azure)
4. **Bot Framework Emulator** (for local testing) — [Download](https://github.com/microsoft/BotFramework-Emulator/releases)

## Quick Start

### Step 1: Register a Bot in Azure

1. Go to [Azure Portal](https://portal.azure.com) → search **"Azure Bot"**
2. Click **Create** → fill in:
   - **Bot handle**: any name
   - **Subscription**: your Azure subscription
   - **Resource group**: create new or use existing
   - **Pricing tier**: F0 (free)
3. After creation, go to **Configuration**:
   - Copy the **Microsoft App ID** → this is your `BOT_ID`
   - Click **Manage** → **Certificates & secrets** → create a new client secret → this is your `BOT_PASSWORD`
4. Go to **Configuration** → set **Messaging endpoint** to:
   ```
   http://localhost:3978/api/messages
   ```

### Step 2: Install Dependencies

```bash
# Clone or navigate to the project directory
cd teams-langchain-bot

# Create a virtual environment (recommended)
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy the example env file
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
BOT_ID=your-azure-bot-app-id
BOT_PASSWORD=your-azure-bot-password
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
PORT=3978
```

### Step 4: Run the Bot

```bash
python -m src.app
```

You should see:

```
Bot server starting on http://localhost:3978
Messages endpoint: http://localhost:3978/api/messages
Press Ctrl+C to stop.
```

### Step 5: Test Locally with Bot Framework Emulator

1. Open **Bot Framework Emulator**
2. Click **Open Bot**
3. Enter bot URL: `http://localhost:3978/api/messages`
4. Leave **Microsoft App ID** and **Microsoft App Password** blank (for local testing)
5. Click **Connect**
6. Send messages and get AI responses

### Step 6: Deploy to Microsoft Teams

#### Option A: Sideload with Teams Toolkit (Recommended)

1. Install [VS Code](https://code.visualstudio.com/) + [Teams Toolkit extension](https://marketplace.visualstudio.com/items?itemName=TeamsDevApp.ms-teams-vscode-extension)
2. Open the project in VS Code
3. Sign in to your Microsoft 365 account via Teams Toolkit
4. Press **F5** to launch in Teams

#### Option B: Manual Sideloading

1. Zip the `appPackage/` folder contents (manifest.json + icons)
2. Go to [Teams Admin Center](https://admin.teams.microsoft.com/policies/manage-apps)
3. Click **Upload new app** → upload your zip
4. Or in Teams: **Apps** → **Manage your apps** → **Upload a custom app**

## Configuration Options

| Variable | Required | Default | Description |
|---|---|---|---|
| `BOT_ID` | Yes | — | Azure Bot Microsoft App ID |
| `BOT_PASSWORD` | Yes | — | Azure Bot client secret |
| `OPENAI_API_KEY` | Yes | — | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model to use |
| `PORT` | No | `3978` | Server port |
| `SYSTEM_PROMPT` | No | (built-in) | Custom system prompt for the bot |

## Architecture

### `src/config.py`
Loads all environment variables into a `Config` class. Single source of truth for configuration.

### `src/langchain_service.py`
- **`ChatOpenAI`** — connects to OpenAI's chat API
- **`ConversationBufferMemory`** — stores full conversation history per Teams conversation ID
- **`ChatPromptTemplate`** — structured prompt with system message, chat history, and user input
- The `chat()` method: loads memory → invokes chain → saves to memory → returns response

### `src/bot.py`
- Extends `ActivityHandler` from Bot Framework SDK
- `on_message_activity` — receives user messages, calls `LangChainService.chat()`, replies
- `on_members_added_activity` — sends welcome message to new users
- Each Teams conversation gets its own memory (context is preserved across messages)

### `src/app.py`
- Creates `BotFrameworkAdapter` with bot credentials
- aiohttp server listens on `/api/messages`
- Deserializes incoming activities, routes to bot handler

## Troubleshooting

| Issue | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'botbuilder'` | Run `pip install -r requirements.txt` in your virtual environment |
| Bot doesn't respond in Emulator | Make sure the server is running and URL is `http://localhost:3978/api/messages` |
| `401 Unauthorized` in Emulator | For local testing, leave App ID/Password blank in Emulator |
| Bot doesn't appear in Teams | Check that the manifest `botId` matches your Azure Bot App ID |
| `OPENAI_API_KEY` error | Verify your key in `.env` starts with `sk-` and is valid |

## License

MIT

run command : 

create the manifest.zip : python build_manifest.py

run command :

terminal 1: python -m src.app
terminal 2: ngrok http 3978
