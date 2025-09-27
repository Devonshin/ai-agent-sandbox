from agents.tool import function_tool

@function_tool
def get_weather(city: str):
  return "30 degrees"
