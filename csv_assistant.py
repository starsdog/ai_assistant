from dotenv import load_dotenv 
from openai import OpenAI
import openai
import os
import time
import pandas as pd
import re
from difflib import SequenceMatcher
from collections import defaultdict

class CSVReader:
    def  __init__(self):
        self.li = []
        self.df = None
        
    def readfile(self, filename):
        frame = pd.read_csv(filename)
        self.li.append(frame)
    
    def import_complete(self):
        self.df = pd.concat(self.li, axis=0, ignore_index=True)
        
    def find_row(self, name):
        for index, row in self.df.iterrows():
             for c in row:
                 if isinstance(c, str) and name.upper() in c:
                     return row
        
        return f"can't find row contains {name}, try find_column with {name}"

    def similar(self, a, b):
        return SequenceMatcher(None, a, b).ratio()
    
    def find_condition(self, operators, raw):
        for op in operators:
            parts = raw.split(op)
            
            if len(parts)>1: 
                operator = op
                right = parts[1]
                return operator, right

        return None, 0


    def find_column(self, condition):
        scores = defaultdict(float)
        for col in self.df:
            score = self.similar(col, condition)
            scores[col] = score

        sorted_score = [k for k, v in sorted(scores.items(), key=lambda item:item[1], reverse=True)]
        print(f"target column = {sorted_score[0]}")
        
        #check if condition exist
        operators = [">=", "<=", ">", "<", "="]
        operator, value = self.find_condition(operators, condition)
        
        print(f"condition={operator}, {value}") 
        if operator != None:
            ## Remove the '%' sign
            target_df = self.df[sorted_score[0]].str.replace("%", "")
            ## Convert to numeric, coercing errors to NaN
            target_df = pd.to_numeric(target_df, errors='coerce')
            target_df = target_df.astype('float')
            
            dest_value = float(value.replace("%", ""))

            if operator == '>':
                filtered_df = self.df[target_df > dest_value]
            elif operator == '<':
                filtered_df = self.df[target_df < dest_value]
            elif operator == '=':
                filtered_df = self.df[target_df == dest_value]
            elif operator == '>=':
                filtered_df = self.df[target_df >= dest_value]
            elif operator == '<=':
                filtered_df = self.df[target_df <= dest_value]
            return filtered_df
        
        return f"can't find column contains {condition}"
        

class CSVAssistant:
    def __init__(self, data_folder):
        self.client = OpenAI()
        self.upload_files = []
        self.csv_reader = CSVReader()
        self.upload(data_folder)
        self.tool = [
            {"type": "retrieval"}, 
            {"type":"code_interpreter"},
            {
                "type": "function",
                "function": {
                    "name": "find_column",
                    "description": "Get the columns which match condition",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "condition": {
                                "type": "string"
                            },
                        },
                        "required": ["condition"],
                    },
                },
            }
        ]
        self.available_functions = {
            "find_column": self.csv_reader.find_column
        } 

        self.worker = self.create_assistant()
    
    def upload(self, folder_path):
        for dirPath, dirNames, fileNames in os.walk(folder_path): 
            for filename in fileNames:
                if ".csv" in filename:
                    file_path=os.path.join(dirPath, filename)
                    file_obj = self.client.files.create(
                        file=open(file_path, 'rb'),
                        purpose='assistants',
                        
                    )
                    self.upload_files.append(file_obj.id)
                    self.csv_reader.readfile(file_path)
        self.csv_reader.import_complete() 
        print(f"upload related file {self.upload_files}")

    def create_assistant(self):
        assistant = openai.beta.assistants.create(
            instructions="You are helping to read transcript files of podcast and answering questions based on information from csv files",
            name="Stock Assistant",
            tools=self.tool,
            model="gpt-4-1106-preview",
            file_ids=self.upload_files,
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

        print(f"query and try to access worker {self.worker}")
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
                        condition=function_args.get("condition")
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
    project_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.join(project_dir, "data", "csv")
    
    assistant = CSVAssistant(data_folder)

    while True:
        question = input('輸入你的問題或是輸入quit離開: ')
        if 'quit' in question:
            break
        assistant.query(question)
        

if __name__== "__main__":
    main()