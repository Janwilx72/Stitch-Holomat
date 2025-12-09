import pygame
import python_weather
import asyncio

import features.home.home_screen as home_screen
from core.assistant_module import jarvis_assist
from icrawler.builtin import GoogleImageCrawler
import os


# ------------ Variables ------------ #
silent_mode_state = False


def toggle_silent_mode(state):
    global silent_mode_state
    silent_mode_state = state
    return f"Silent mode {'enabled' if state else 'disabled'}."


def is_silent_mode():
    return silent_mode_state


async def get_weather(city_name):
    async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
        weather = await client.get(city_name)
        return weather


def search(query):
    google_crawler = GoogleImageCrawler(storage={"root_dir": r'./images'})
    google_crawler.crawl(keyword=query, max_num=1)


# Web search functions
def perform_web_search(query, num_results=3):
    try:
        results = list(search(query, num_results=num_results, advanced=True))
        return [{'title': r.title, 'description': r.description, 'url': r.url} for r in results]
    except Exception as e:
        print(f"Error performing web search: {e}")
        return []


def web_search(query):
    results = perform_web_search(query)
    if results:
        return "\n".join([f"Title: {r['title']}\nDescription: {r['description']}" for r in results])
    return f"No results found for '{query}'"


def parse_command(command):
    print('Parsing Command: ', command)

    if "weather" in command:
        weather_description = asyncio.run(get_weather("Chicago"))
        query = "System information: " + str(weather_description)
        print(query)
        response = jarvis_assist.ask_question_memory(query)
        done = jarvis_assist.TTS(response)
        return tuple([True, ""])

    if "search" in command:
        files = os.listdir("./images")
        [os.remove(os.path.join("./images", f)) for f in files]
        query = command.split("-")[1]
        search(query)

    if "open" in command and "home" in command:
        home_screen.JARVIS_COMMANDS_MAP["home_command"] = True
        print('opening home: ', home_screen.JARVIS_COMMANDS_MAP)

        # home_screen.set_jarvis_home_command()
        return tuple([True, "Home Menu Opened"])

    if "close" in command and "home" in command:
        home_screen.JARVIS_COMMANDS_MAP["home_command"] = True
        print('closing home: ', home_screen.JARVIS_COMMANDS_MAP)
        has_run = True
        return tuple([True, "Home Menu Opened"])

    if "run" in command and ("app" or "application") in command and "cooking" in command:
        home_screen.JARVIS_COMMANDS_MAP["jarvis_app_index"] = 5
        return tuple([True, "Running Application"])

    return tuple([False, ""])



