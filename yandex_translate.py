from flask import Flask, request
import logging
import json

app = Flask(__name__)
sessionStorage = {}

logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s %(levelname)s %(name)s %(message)s')


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)

    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    handle_dialog(response, request.json)

    logging.info('Request: %r', response)

    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response'][
            'text'] = 'Здарова, оболтус!' \
                      ' Пиши сюда свой текст и я его переведу,' \
                      ' а потом позвоню твоей маме и расскажу, что ты не учишь английский!!!'
        sessionStorage[user_id] = {
            'tft': None
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        tft = get_text(req)
        if req['request']['original_utterance'].lower() == 'помощь':
            res['response']['text'] = 'Бог тебе в помощь'
            return
        if tft is None:
            res['response']['text'] = 'Не расслышала текст. Повтори, пожалуйста!'
            res['response']['buttons'] = [
                {
                    'title': 'Помощь',
                    'hide': True
                }
            ]
        if len(tft) != 3:
            res['response'][
                'text'] = "Чтобы запрос прошел тебе всего лишь нужно сказать: 'Переведи слово" \
                          " (ваше слово, которое нужно перевести)'"
        else:
            translate(tft[2])
        return


def translate(text):
    url = "https://translate.yandex.net/api/v1.5/tr.json/translate"

    params = {
        "key": "trnsl.1.1.20190416T140835Z.08c28d20c7acdc1f.0cd411bb3df4733f9798dcdb262b93f64b5f3225",
        "text": text,
        "lang": "en",
        "format": "plain"
    }

    response = request.post(url, params)

    return eval(response.text["text"])


def get_text(req):
    text = []

    for entity in req['request']:
        text.append(entity)
    return text


if __name__ == '__main__':
    app.run()
