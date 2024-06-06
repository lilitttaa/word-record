import json
import time
from g4f.client import Client
import g4f.debug
g4f.debug.logging = True
from openai import OpenAI

with open("config.json", "r",encoding="utf-8") as f:
    config = json.load(f)
    MOONSHOT_API_KEY = config["MOONSHOT_API_KEY"]
    WORD_SAVE_PATH = config["WORD_SAVE_PATH"]


def request_interpret_g4f(word, context):
    client = Client()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": "".join(
                    [
                        "Please interpret the meaning of the word {",
                        word,
                        "} in the context {",
                        context,
                        "}",
                        "{",
                        word,
                        "} means",
                    ]
                ),
            }
        ],
    )
    return response.choices[0].message.content


def write_to_jsonl(word, context, interpret):
    obj = {
        "word": word,
        "context": context,
        "interpret": interpret,
        "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
    }
    json_obj = json.dumps(obj, ensure_ascii=False)

    with open( WORD_SAVE_PATH + "/word_record.jsonl", "a",encoding="utf-8") as f:
        f.write(json_obj + "\n")

def retry_request(times: int, interval: int = 1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print('retry request')
                    time.sleep(interval)
                    continue
            raise Exception('retry request failed')
        return wrapper
    return decorator


class InterpretGenerator:
    def __init__(self):
        self._client = OpenAI(
            api_key=MOONSHOT_API_KEY,
            base_url="https://api.moonshot.cn/v1",
        )

    def generate_interpret(self, word, context):
        if not self._check_valid(word):
            raise Exception("Invalid input word")
        if not self._check_valid(context):
            raise Exception("Invalid input context")
        return self._request_interpret(word, context)

    @retry_request(3, 3)
    def _request_interpret(self, word, context):
        completion = self._client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=[
                {
                    "role": "user",
                    "content": "".join(
                        [
                            "Please interpret the meaning of the word briefly{",
                            word,
                            "} in this context {",
                            context,
                            "}",
                            "{",
                            word,
                            "} means",
                        ]
                    ),
                }
            ],
            temperature=0.3,
        )
        return completion.choices[0].message.content

    def _check_valid(self, text):
        text = text.strip()
        if text == "":
            print("Invalid input", text)
            return False
        return True

def main():
    while True:
        word = input("- Please input the word you want to record:")
        print("\n")
        context = input("- Please input the context:")
        print("\n")
        try:
            generator = InterpretGenerator()
            interpret = generator.generate_interpret(word, context)
        except Exception as e:
            continue
        print(interpret)
        print("\n")
        write_to_jsonl(word, context, interpret)

if __name__ == "__main__":
    main()
