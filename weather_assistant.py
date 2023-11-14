from dotenv import load_dotenv 
from openai import OpenAI
import openai
import os
import time
import json

class WeatherAssistant:
    def __init__(self):
        self.client = OpenAI()
        self.tool = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Get the current weather in a given location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA",
                            },
                            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                        },
                        "required": ["location"],
                    },
                },
            }
        ]
        self.available_functions = {
            "get_current_weather": self.get_current_weather,
        } 
        self.worker = self.create_assistant()
    
    def get_current_weather(self, location, unit="fahrenheit"):
        """Get the current weather in a given location"""
        if "tokyo" in location.lower():
            return json.dumps({"location": "Tokyo", "temperature": "10", "unit": "celsius"})
        elif "san francisco" in location.lower():
            return json.dumps({"location": "San Francisco", "temperature": "72", "unit": "fahrenheit"})
        elif "paris" in location.lower():
            return json.dumps({"location": "Paris", "temperature": "22", "unit": "celsius"})
        else:
            return json.dumps({"location": location, "temperature": "unknown"})
    
    def create_assistant(self):
        assistant = openai.beta.assistants.create(
            instructions="You are using function call to query weather info",
            name="Weather Assistant",
            tools=self.tool,
            model="gpt-4-1106-preview"
        )
                            
        return assistant
    
    def query(self, question):
        print(f"query is {question}")
        thread = openai.beta.threads.create()
        thread_id = thread.id

        message = self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=question,
        )

        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.worker.id)
        
        print(f"assistant starts running...")
        start = time.time()
        is_answer = False
        while True:
            run = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            if run.required_action:
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_to_call = self.available_functions[function_name]
                    function_args = json.loads(tool_call.function.arguments)
                    function_response = function_to_call(
                        location=function_args.get("location"),
                        unit=function_args.get("unit"),
                    )
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output":function_response
                    })
                run = self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id, 
                    run_id=run.id, 
                    tool_outputs=tool_outputs)
        
            if run.completed_at:
                elapsed = run.completed_at - run.created_at
                elapsed = time.strftime("%H:%M:%S", time.gmtime(elapsed))
                print(f"Run completed in {elapsed}")
                is_answer = True
                break
            time.sleep(1)
            current = time.time()
            
            if current-start > 30:
                print(f"wait timeout! Can't get answer this time")
                break
        if is_answer:
            messages = self.client.beta.threads.messages.list(thread_id=thread_id)
            last_message = messages.data[0]

            text = last_message.content[0].text.value
            print(f"final answer: {text}")


def main():
    load_dotenv() 
    assistant = WeatherAssistant()

    question = "What's the weather like in San Francisco, Tokyo, and Taipei? "
    assistant.query(question)
    

if __name__== "__main__":
    main()