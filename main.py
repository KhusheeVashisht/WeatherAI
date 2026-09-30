"""
main.py - CLI Application & LLM Tool-Calling Orchestrator

This file implements the interactive CLI loop. It initializes the Gemini LLM via 
google-genai SDK, defines the weather tool schema, intercepts model tool-call 
requests, executes the weather tool in Python, sends structured results back to 
the model, and outputs the final natural-language response.
"""

import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

from weather import get_weather

# Load environment variables from .env file
load_dotenv()

SYSTEM_INSTRUCTION = """
You are a helpful conversational AI assistant equipped with real-time weather integration.

TOOL CALLING RULES:
1. When a user asks for current weather or weather conditions (temperature, rain, humidity, wind, etc.) for a specific city or location, call the `get_weather` tool.
2. If the user asks for weather info but DOES NOT provide a city or location, DO NOT call the `get_weather` tool and DO NOT guess or invent a location. Ask a polite clarifying question to find out which city they want the weather for.
3. If the user provides a city in a follow-up turn (e.g. User asks "What's the weather?" -> You ask "Which city?" -> User answers "Hyderabad"), recognize this as a follow-up to the weather request and call `get_weather` for that city.
4. For general non-weather queries (e.g., coding, math, general facts like "What is machine learning?"), answer directly without calling any tools.
5. When synthesizing response from tool data, summarize the temperature, description, humidity, and wind speed in clear, friendly conversational language.
"""


def print_header():
    """Print welcoming CLI banner."""
    print("=" * 65)
    print("   🌤️  LLM Tool-Calling CLI Application (Weather Assistant)   ")
    print("=" * 65)
    print("Ask weather queries (e.g., 'What's the weather in Hyderabad?')")
    print("or general questions. Type 'exit' or 'quit' to terminate.\n")


def check_environment():
    """Verify that required API keys are configured before starting."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    weather_key = os.getenv("OPENWEATHER_API_KEY")

    missing = []
    if not gemini_key:
        missing.append("GEMINI_API_KEY")
    if not weather_key:
        missing.append("OPENWEATHER_API_KEY")

    if missing:
        print("[ERROR] Missing required environment variable(s): " + ", ".join(missing))
        print("Please copy '.env.example' to '.env' and populate your API keys.")
        print("Application exiting.\n")
        sys.exit(1)


def run_cli():
    """Run the main interactive conversational loop with explicit tool execution."""
    check_environment()
    print_header()

    # Initialize Gemini client
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Configure model session with tools and explicit function calling (disable automatic calling)
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=[get_weather],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        temperature=0.2,  # Low temperature ensures reliable tool invocations
    )

    # Initialize multi-turn chat session using gemini-2.5-flash
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=config
    )

    while True:
        try:
            user_input = input("User: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nGoodbye!")
                break

            # 1. Send user prompt to LLM
            response = chat.send_message(user_input)

            # 2. Inspect if LLM generated tool-call request(s)
            if response.function_calls:
                for call in response.function_calls:
                    fn_name = call.name
                    fn_args = call.args or {}

                    print(f"\n⚙️  [LLM Tool Decision] Function: `{fn_name}`, Arguments: {fn_args}")

                    if fn_name == "get_weather":
                        city = fn_args.get("city")
                        if not city:
                            tool_result = {"error": "Missing required argument 'city'."}
                        else:
                            print(f"🌐 [Tool Execution] Calling OpenWeatherMap API for location: '{city}'...")
                            tool_result = get_weather(city)

                        print(f"📊 [Tool Result Payload]: {tool_result}\n")

                        # 3. Return structured tool execution result back to LLM
                        final_response = chat.send_message(
                            types.Part.from_function_response(
                                name=fn_name,
                                response={"result": tool_result}
                            )
                        )
                        print(f"Assistant: {final_response.text}\n")
                    else:
                        print(f"[Error] Unknown tool requested by model: {fn_name}\n")
            else:
                # 4. LLM responded directly without tool call (e.g. non-weather query or clarification)
                print(f"\nAssistant: {response.text}\n")

        except KeyboardInterrupt:
            print("\nSession interrupted by user. Exiting...")
            break
        except Exception as err:
            print(f"\n[Error] An error occurred during chat turn: {err}\n")


if __name__ == "__main__":
    run_cli()
