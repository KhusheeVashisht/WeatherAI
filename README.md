# Weather AI: Reliable LLM Tool-Calling CLI Application

A lightweight, clean, and robust Python CLI application demonstrating **LLM Tool Calling (Function Calling)** using Google's modern **Gemini API** (`google-genai` SDK) and the **OpenWeatherMap REST API**.

---

## 📌 Project Overview

This project demonstrates how a Large Language Model (LLM) can dynamically decide when to delegate requests to external code tools to answer queries requiring real-time external data (such as current weather conditions).

### Key Features
- **Reliable Tool Calling**: Automatically detects when a user query requires real-time weather information and extracts parameters cleanly.
- **Strict Parameter Handling**: Never guesses missing locations. If a location is omitted, the assistant asks a natural clarifying question.
- **Conversational Memory**: Remembers context across multi-turn interactions (e.g., handles follow-up location answers naturally).
- **Graceful Error Handling**: Manages invalid cities (404), network timeouts, invalid API keys, and missing arguments without crashing.
- **Non-Weather Routing**: Directly answers general queries (e.g., "What is machine learning?") without invoking external weather APIs unnecessarily.

---

## 🏗️ Architecture & Core Tool-Calling Flow

```
+--------------+               +---------------+               +--------------------+
|  User (CLI)  |  --(Prompt)-> |  Gemini LLM   |  -(ToolCall)->| Application (Python)|
+--------------+               +---------------+               +--------------------+
       ^                                                                 |
       |                                                         (REST HTTP Request)
       |                                                                 v
+--------------+               +---------------+               +--------------------+
| Final Answer |  <--(Text)--  |  Gemini LLM   |  <-(Payload)- | OpenWeatherMap API |
+--------------+               +---------------+               +--------------------+
```

### Step-by-Step Lifecycle
1. **User Prompt**: User enters a natural language query in the CLI (e.g., *"What's the weather in Hyderabad?"*).
2. **LLM Evaluation**: Gemini receives the user query alongside registered tool declarations.
3. **Tool Call Decision**: 
   - If live weather data is needed **and** location is provided, the LLM generates a structured `FunctionCall` request (`get_weather(city="Hyderabad")`).
   - If location is **missing**, the LLM responds with a natural clarification request instead of calling the tool.
   - If the question is non-weather, the LLM answers directly without calling the tool.
4. **Tool Execution (Client Application)**: The Python application intercepts the `FunctionCall`, executes `get_weather("Hyderabad")`, and fetches live data from OpenWeatherMap.
5. **Tool Result Returned to LLM**: The application converts the structured result into a `FunctionResponse` payload and sends it back to the Gemini chat session.
6. **Final Natural-Language Synthesis**: Gemini consumes the weather data payload and generates a friendly, conversational answer for the user.

---

## ❓ Why Can't LLMs Directly Know Live Weather?

1. **Static Knowledge Cutoff**: LLM training weights are static and cannot predict real-time dynamic state like current temperature or rain.
2. **Lack of Native Network Access**: LLMs run in isolated inference environments without direct Internet access or API execution capabilities.
3. **Role of Tool Calling**: Tool calling bridges the gap between LLM reasoning and real-world real-time data services, allowing the application to act as an execution proxy.

---

## 🛠️ Tool Definition & Execution

### Tool Definition (`weather.py`)
The tool is defined as a standard Python function with type hints and docstrings:

```python
def get_weather(city: str) -> Dict[str, Any]:
    """Fetch current weather data for a specified city using OpenWeatherMap API.

    Args:
        city (str): The name of the city or location (e.g., 'Hyderabad', 'London', 'Tokyo').
    """
```

### How Tool Definition is Registered
In `main.py`, `get_weather` is registered in `types.GenerateContentConfig`:

```python
config = types.GenerateContentConfig(
    system_instruction=SYSTEM_INSTRUCTION,
    tools=[get_weather],
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
)
```

Setting `automatic_function_calling` to `disable=True` ensures that the Python application explicitly controls execution, inspection, and feedback logging during interview demonstrations.

### Returning Results Back to LLM
When `get_weather` finishes, its JSON result dictionary is passed back to Gemini using:

```python
chat.send_message(
    types.Part.from_function_response(
        name="get_weather",
        response={"result": tool_result}
    )
)
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.9+
- Gemini API Key ([Get free key from Google AI Studio](https://aistudio.google.com/))
- OpenWeatherMap API Key ([Get free key from OpenWeatherMap](https://openweathermap.org/api))

### 2. Installation Steps
Clone or download the project folder, then navigate into the directory:

```bash
cd weatherai
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

### 3. Environment Variable Configuration
Copy `.env.example` to create `.env`:

```bash
cp .env.example .env
```

Edit `.env` and fill in your actual API keys:

```env
GEMINI_API_KEY=your_actual_gemini_api_key
OPENWEATHER_API_KEY=your_actual_openweather_api_key
```

### 4. Run the CLI Application
Run `main.py`:

```bash
python main.py
```

---

## 💬 Example CLI Interactions

### Scenario 1: Direct Weather Query
```text
User: What's the weather in Hyderabad?

⚙️  [LLM Tool Decision] Function: `get_weather`, Arguments: {'city': 'Hyderabad'}
🌐 [Tool Execution] Calling OpenWeatherMap API for location: 'Hyderabad'...
📊 [Tool Result Payload]: {'city': 'Hyderabad', 'country': 'IN', 'temperature_celsius': 31.2, 'feels_like_celsius': 33.5, 'humidity_percent': 58, 'description': 'scattered clouds', 'wind_speed_m_s': 3.6, 'status': 'success'}

Assistant: Currently in Hyderabad, India, it's 31.2°C (feels like 33.5°C) with scattered clouds. Humidity is at 58% and wind speed is around 3.6 m/s.
```

### Scenario 2: Weather Request Without Location & Follow-Up
```text
User: What's the weather?

Assistant: Sure! Which city or location would you like the weather for?

User: Hyderabad

⚙️  [LLM Tool Decision] Function: `get_weather`, Arguments: {'city': 'Hyderabad'}
🌐 [Tool Execution] Calling OpenWeatherMap API for location: 'Hyderabad'...
📊 [Tool Result Payload]: {'city': 'Hyderabad', 'country': 'IN', 'temperature_celsius': 31.2, ...}

Assistant: The weather in Hyderabad is currently 31.2°C with scattered clouds...
```

### Scenario 3: Non-Weather Query
```text
User: Explain machine learning in simple terms.

Assistant: Machine learning is a field of artificial intelligence where computers learn patterns from data to make decisions or predictions without being explicitly programmed for every scenario...
```

### Scenario 4: Invalid Location
```text
User: What's the weather in XYZABC?

⚙️  [LLM Tool Decision] Function: `get_weather`, Arguments: {'city': 'XYZABC'}
🌐 [Tool Execution] Calling OpenWeatherMap API for location: 'XYZABC'...
📊 [Tool Result Payload]: {'error': "City 'XYZABC' was not found by OpenWeatherMap. Please check the spelling."}

Assistant: I couldn't find weather data for 'XYZABC'. Please make sure the city name is spelled correctly!
```

---

## 🎯 Design Decisions & Trade-offs

1. **Official `google-genai` SDK over Deprecated Packages**: Built using Google's current `google-genai` SDK (`genai.Client`) for long-term stability and modern type support.
2. **Explicit Tool Execution vs. Automatic Function Calling**: Set `automatic_function_calling=disable=True` so that the execution loop explicitly demonstrates parameter extraction, API calls, and payload passing.
3. **System Instruction Guardrails**: Provided explicit prompt guardrails instructing the LLM never to guess missing locations or trigger weather tools on non-weather prompts.
4. **Minimal External Dependencies**: Kept to `google-genai`, `requests`, and `python-dotenv` to eliminate unnecessary framework bloat.

---

## ⚠️ Limitations

- **Rate Limits**: Subject to free-tier rate limits of Gemini API and OpenWeatherMap API.
- **Single Tool Scope**: Designed strictly around the weather function for assessment clarity.
- **CLI Interface**: Uses stdio terminal interaction without a GUI/Web interface as per assessment scope.
