from dotenv import load_dotenv 
from openai import OpenAI
import openai
import os
import time

class PodcastAssistant:
    def __init__(self, data_folder):
        self.client = OpenAI()
        self.upload_files = []
        self.upload(data_folder)
        self.worker = self.create_assistant()
    
    def upload(self, folder_path):
        for dirPath, dirNames, fileNames in os.walk(folder_path): 
            for filename in fileNames:
                if ".srt" in filename:
                    file_path=os.path.join(dirPath, filename)
                    file_obj = self.client.files.create(
                        file=open(file_path, 'rb'),
                        purpose='assistants',
                        
                    )
                    self.upload_files.append(file_obj.id)
        print(f"upload related file {self.upload_files}")

    def create_assistant(self):
        assistant = openai.beta.assistants.create(
            instructions="You are helping to read transcript files of podcast and answering questions based on information from srt files",
            name="MINEBOOK Podcast Assistant",
            tools=[{"type": "retrieval"}],
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

        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.worker.id)
        
        print(f"assistant starts running...")
        start = time.time()
        is_answer = False
        while True:
            run = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
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
    data_folder = os.path.join(project_dir, "data", "srt")
    
    assistant = PodcastAssistant(data_folder)

    while True:
        question = input('輸入你的問題或是輸入quit離開: ')
        if 'quit' in question:
            break
        assistant.query(question)
        

if __name__== "__main__":
    main()