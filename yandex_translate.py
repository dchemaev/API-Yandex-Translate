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
        res['response']['text'] = 'Привет! Назови своё имя!'
        sessionStorage[user_id] = {
            'tft': None,
            'first_name': None
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        if req['request']['original_utterance'].lower() == 'помощь':
            res['response']['text'] = 'Бог тебе в помощь'
            return
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
            res['response']['buttons'] = [
                {
                    'title': 'Помощь',
                    'hide': True
                }
            ]
            return
        else:
            sessionStorage[user_id]['first_name'] = first_name
            # создаём пустой массив, в который будем записывать города, которые пользователь уже отгадал
            res['response'][
                'text'] = f'Приятно познакомиться, {first_name.title()}, шучу, мне плевать как тебя зовут.' \
                f' Я буду называть тебя оболтусом'

            res['response'][
                'text'] = 'Здарова, оболтус!' \
                          ' Пиши сюда свой текст и я его переведу,' \
                          ' а потом позвоню твоей маме и расскажу, что ты не учишь английский!!!'
        tft = get_text(req)
        if tft is None:
            res['response']['text'] = 'Не расслышала текст. Повтори, пожалуйста!'
            res['response']['buttons'] = [
                {
                    'title': 'Помощь',
                    'hide': True
                }
            ]
            return
        sessionStorage[user_id]['tft'] = tft
        res['response']['text'] = f'{translate(tft)}'


def translate(text):
    url = "https://translate.yandex.net/api/v1.5/tr.json/translate"

    params = {
        "key": "trnsl.1.1.20190416T140835Z.08c28d20c7acdc1f.0cd411bb3df4733f9798dcdb262b93f64b5f3225",
        "text": text,
        "lang": "en",
        "format": "plain"
    }

    response = request.get(url, params)
    logging.info(eval(response)['text'][0])
    return eval(response)['text'][0]  # translated text


def get_text(req):
    text = []
    for word in req['request']['nlu']['tokens']:
        text.append(word)
    if len(text) == 3:
        return text[2]


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name', то возвращаем её значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()
