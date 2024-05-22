import json
import time
from pynput import mouse, keyboard
import pyperclip

drag_flag = True
mouse_press = (0, 0)
mouse_release = (0, 0)
record_txt = ""

with open("config.json", "r") as f:
    config = json.load(f)
    MOONSHOT_API_KEY = config["MOONSHOT_API_KEY"]


def get_select_text():
    cache = pyperclip.paste()

    control = keyboard.Controller()
    with control.pressed(keyboard.Key.ctrl):
        control.press("c")
        control.release("c")
    time.sleep(0.1)
    text = pyperclip.paste()
    pyperclip.copy(cache)
    return text


def on_click(x, y, button, pressed):
    global drag_flag, mouse_press, mouse_release, record_txt
    if pressed:
        mouse_press = (x, y)
        return
    else:
        mouse_release = (x, y)
        if mouse_press != mouse_release:
            record_txt = get_select_text()


from plyer import notification
from g4f.client import Client
import g4f.debug

g4f.debug.logging = True


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


def request_interpret_moonshot(word,context):
    from openai import OpenAI
    
    client = OpenAI(
        api_key=MOONSHOT_API_KEY,
        base_url="https://api.moonshot.cn/v1",
    )
    
    completion = client.chat.completions.create(
        model="moonshot-v1-32k",
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
        temperature=0.3,
    )
    return completion.choices[0].message.content



class WordRecord:
    def __init__(self) -> None:
        self._word: str = ""
        self._context: str = ""
        self._interpret: str = ""
        self._record_txt: str = ""
        self._mouse_press = (0, 0)
        self._mouse_release = (0, 0)

    def _get_select_text(self):
        cache = pyperclip.paste()

        control = keyboard.Controller()
        with control.pressed(keyboard.Key.ctrl):
            control.press("c")
            control.release("c")
        time.sleep(0.1)
        text = pyperclip.paste()
        pyperclip.copy(cache)
        return text

    def on_click(self, x, y, button, pressed):
        if pressed:
            self._mouse_press = (x, y)
            self._record_txt = ""
        else:
            self._mouse_release = (x, y)
            self._record_txt = self._get_select_text()

    def _show_notification(self, title, message):
        print("show_notification")
        notification.notify(
            title=title,
            message=message,
            app_icon=None,
            timeout=1,
        )

    def record_word(self):
        print("record_word")
        self._word = self._record_txt

    def record_context(self):
        print("record_context")
        self._context = self._record_txt

        if self._word == "" or self._context == "":
            self._show_notification("错误", "未选择单词或Context")
        else:
            self._interpret = request_interpret_moonshot(self._word, self._context)
            self._show_notification(
                "记录成功",
                "".join(
                    [
                        "单词：",
                        self._word,
                        "\n",
                    ]
                ),
            )
            self._write_to_jsonl()
        self._word = ""
        self._context = ""
        self._interpret = ""

    def _write_to_jsonl(self):
        obj = {
            "word": self._word,
            "context": self._context,
            "interpret": self._interpret,
        }
        json_obj = json.dumps(obj)
        with open("record.jsonl", "a") as f:
            f.write(json_obj + "\n")


def main():
    word_record = WordRecord()
    listener = mouse.Listener(
        on_click=lambda x, y, button, pressed: word_record.on_click(
            x, y, button, pressed
        )
    )
    listener.start()
    with keyboard.GlobalHotKeys(
        {
            "<ctrl>+<shift>+<alt>+q": lambda: word_record.record_word(),
            "<ctrl>+<shift>+<alt>+w": lambda: word_record.record_context(),
        }
    ) as h:
        h.join()


if __name__ == "__main__":
    main()
