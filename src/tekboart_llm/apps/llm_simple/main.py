import sys
import os
# TODO: Use pyproject.toml instead of sys.path.append hack
# https://stackoverflow.com/questions/714063/importing-modules-from-parent-folder
ROOT_LVL = os.path.join("..", "..")
sys.path.append(ROOT_LVL)

#  from utils.format.response import response_structure
#  from utils.llm.ollama import ollama_model_call

from tekboart_llm.utils.format.response import response_structure
from tekboart_llm.model.ollama import ollama_model_call

from utils.response import response_structure
from utils.llm.ollama import ollama_model_call

if __name__ == "__main__":

    # Choose the model
    models = [
            'llama3.2',
            'deepseek-r1:1.5b',
            'deepseek-r1:7b',
            'deepseek-r1:14b',
            'deepseek-r1:32b',
    ]

    print("Choose the LLM: (default (1))")
    print("Options:")
    for idx, x in enumerate(models, start=1):
        print(f'({idx}) {x}')
    print()

    MODEL_NAME = models[int(input("Enter the number (e.g., 1):") or "1") - 1]
    print(f'{MODEL_NAME = }')
    print(79*"-")

    # Pass in the prompt
    # prompt = input("enter your prompt:")
    prompt = input("Enter your prompt:\n")
    print(79*"-")

    # Give the prompt to an LLM
    print(79*"-", "\nLLM thinking ;)\n", sep="")
    response_raw = ollama_model_call(prompt, model=MODEL_NAME)
    response = response_raw['message']['content']
    print(79*"-", "\nResponse generated with success\n", 79*"-", sep="")

    # Save the response to a file
    # Note: the response is in Markdown format. You can use an online Markdown editor to view them better (e.g. https://stackedit.io/).
    if response_raw:
        with open('response.md', 'w') as f:
            f.write(response_structure.format(
                MODEL_NAME=MODEL_NAME, prompt=prompt, response=response))
