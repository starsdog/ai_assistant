# AI Assistant

Referencing OpenAI Assistant, I create my own ai assistant

### Setup
1. `pipenv shell`
2. `pipenv install`
3. need to update open api key in `.env.example` and change to `.env`

### How to use

- Podcast Assistant: This assistant reads transcript files of podcast and answers related questions about podcast
  - sample question: the name of podcast, how many books does the podcast introduce
- Weather Assistant: This assistant is using function call to answer related questions
- Image Assistant: This assistant creates images based on prompt 
- CSV Assistant: 
  - sample question: which stock gain > 60%, gain of AAPL

### Reference
[OpenAI Assistant](https://platform.openai.com/docs/assistants/overview)