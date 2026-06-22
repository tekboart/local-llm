from ollama import chat, pull
from ollama import ChatResponse
from ollama import ResponseError

import os

# TODO: Keep the chat history (by using the "stream" keyword)
def ollama_model_call(prompt, model: str ='llama3.2', images_path: str = None):
    flag = True
    while flag:
        try:
            # TODO: add logging INFO
            # e.g., [Calling the model with the prompt]
            # print('try: call model')
            response: ChatResponse = chat(model=model, messages=[
            {
                'role': 'user',
                'content': prompt,
                # TODO: activate only for multi-modal models (e.g., 'llama3.2-vision)
                # 'images': [IMAGE_PATH] if isinstance(str, images_path) else None

            },
            #TODO: enable 'model streaming'--for interactive prompting
            # https://medium.com/@revlae/how-to-stop-ollama-model-streaming-600a222b4797
            # stream=True,
            ])
            flag=False
        except ResponseError as e:
            print('except: call model')
            print('Error:', e.error)
            if e.status_code == 404:
                # TODO: add logging WARNING
                # e.g., [the model:{} is not installed. Now trying to pull it from Ollama server]
                try:
                    print('try: pull model')
                    print(f'======= Pulling the {model}: Start ======')
                    pull(model)
                    print(f'======= Pulling the {model}: End ======')
                except Exception as e2:
                    print('except: pull model')
                    print(f'{type(e2)}: {e2}')
                    break
            else:
                print('no e.status_code == 404')
                # TODO: add logging DEBUG
                break
    else:
        # TODO: add logging INFO
        print(f'Successful: Got the response from "{model}" with no Error')
        return response