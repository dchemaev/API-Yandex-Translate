from flask import Flask, request
import logging
import requests
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
    user_id = req['session']['user_id']  # Получаем ID пользователя

    """""
    Проверяем, если пользователь новый, то мы получаем его имя, проверяя с помощью сущностей API
    """""
    if req['session']['new']:
        res['response'][
            'text'] = 'Привет! Я переводчик слов, для начала назови мне своё имя,' \
                      ' а после напиши мне "Переведи слово [Ваше слово] и язык(en, en итп)!'
        sessionStorage[user_id] = {
            'tft': None,
            'first_name': None
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        if req['request']['original_utterance'].lower() == 'помощь':
            res['response']['text'] = 'Просто напиши мне своё имя'
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
            """"" 
            Мы получили правильное имя пользователя, и просим его ввести слово для перевода в формате: \
                "Переведи текст ..."
            """""
            sessionStorage[user_id]['first_name'] = first_name
            res['response'][
                'text'] = f'Приятно познакомиться, {first_name.title()}.' \
                f' Пиши сюда свой текст и я его переведу.'
            res['response']['buttons'] = [
                {
                    'title': 'Помощь',
                    'hide': True
                },
                {
                    'title': 'Что ты умеешь?',
                    'hide': True
                }
            ]
            return
    else:

        if req['request']['original_utterance'].lower() == 'помощь':
            res['response']['text'] = 'Просто напиши мне "Переведи слово [Ваше слово] и язык,' \
                                      ' на котором хочешь перевести(es, en итд)'
            return
        if req['request']['original_utterance'].lower() == 'переведено сервисом яндекс.переводчик':
            res['response']['text'] = 'Перехожу на официальный сайт Яндекс.Переводчика'
            return
        if req['request']['original_utterance'].lower() == 'что ты умеешь?':
            res['response']['text'] = 'Я могу перевести любое слово на любой язык мира'
            return
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
        else:
            if len(tft) == 1:
                sessionStorage[user_id]['tft'] = tft[0]
                ttext = sessionStorage[user_id]["tft"]
                llang = "ru-en"
                res['response']['text'] = f'{translate(ttext, llang)}'
                res['response']['buttons'] = [
                    {
                        'title': 'Переведено сервисом Яндекс.Переводчик',
                        'hide': True,
                        'url': "http://translate.yandex.ru/"
                    }]
                return
            else:
                sessionStorage[user_id]['tft'] = tft[0]
                sessionStorage[user_id]['lang'] = tft[1]
                ttext = sessionStorage[user_id]["tft"]
                llang = sessionStorage[user_id]["lang"]
                res['response']['text'] = f'{translate(ttext, llang)}'
                res['response']['buttons'] = [
                    {
                        'title': 'Переведено сервисом Яндекс.Переводчик',
                        'hide': True,
                        'url': "http://translate.yandex.ru/"
                    }]
                return


def translate(text, llang) -> "Перевод текста":
    url = "https://translate.yandex.net/api/v1.5/tr.json/translate"
    params = {
        "key": "trnsl.1.1.20190416T140835Z.08c28d20c7acdc1f.0cd411bb3df4733f9798dcdb262b93f64b5f3225",
        "text": text,
        "lang": llang,
        "format": "plain"
    }

    response = requests.get(url, params=params)
    logging.info(response)
    return response.json()['text'][0]  # translated text


def get_text(req) -> "Получение текста для перевода":
    text = []
    for word in req['request']['nlu']['tokens']:
        text.append(word)
    if len(text) == 4:
        return text[2], text[3]
    if len(text) == 3:
        return text[2]
    else:
        return None


def get_first_name(req) -> "Получение имени пользователя":
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name', то возвращаем её значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()
