import json
import requests

from django.conf import settings
from .models import Message, MessageHistory, UserProfile
from celery.task import periodic_task
from datetime import timedelta
from django.utils import timezone


@periodic_task(run_every=timedelta(minutes=settings.MAILGUN_LIBRARY_RETRY_MINUTES))
def do_sync_log_with_mailgun():
    # Максимальное количество событий за один запрос
    LIMIT = 300

    url = 'https://api.mailgun.net/v3/' + settings.MAILGUN_DOMAIN_NAME + '/events'
    # Дополнительные поля запроса к mailgun
    start_date = timezone.now() - timedelta(minutes=settings.MAILGUN_LIBRARY_RETRY_MINUTES * 2)
    querystring = {"limit": LIMIT,
                   "ascending": "yes",
                   "begin": start_date.strftime('%a, %d %B %Y %H:%M:%S %Z')}

    # Получение всего списка истории
    response = requests.request("GET", url, auth=('api', settings.MAILGUN_API_KEY), params=querystring)
    status_list = []
    if response.status_code == 200:
        current = json.loads(response.text)

        status_list.extend(current['items'])
        while len(current['items']) == LIMIT:
            url = current['paging']['next']
            response = requests.request("GET", url, auth=('api', settings.MAILGUN_API_KEY))
            if response.status_code == 200:
                current = json.loads(response.text)
                status_list.extend(current['items'])
            else:
                current['items'] = []

    for item in status_list:
        # Добавление информации о сообщении
        message = Message.add_new_message(item['message']['headers'], item['storage'])
        if message:
            # Добавление статуса письма
            MessageHistory.add_new_log(message, item)
            # Делаем отметку если аккаунт не настоящий
            if item['event'] == 'failed' and (item['delivery-status']['description'] == "MX lookup failed" or
                                              item['reason'] == 'bounce' or item['reason'] == 'suppress-bounce'):
                UserProfile.set_fake_status(message.to, item['delivery-status']['description'])
