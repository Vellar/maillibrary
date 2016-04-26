from django.utils import timezone
from datetime import datetime
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist


class Message(models.Model):
    """
    Модель отправленного письма
    """
    message_id = models.CharField('ID письма', max_length=35, unique=True)
    to = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Пользователь')
    subject = models.CharField('Тема письма', max_length=250)
    url = models.URLField('url письма')
    key = models.CharField('storage key', max_length=250)

    class Meta:
        verbose_name = 'Письмо'
        verbose_name_plural = 'Письма'

    def last_event(self):
        """
        :return: последний статус
        """
        return self.messagehistory_set.all()[0].get_color_event()

    last_event.short_description = 'Последний статус'
    last_event.allow_tags = True

    @classmethod
    def add_new_message(cls, headers, storage):
        """
        Добавление нового письма или возврат существующего
        """
        message = False
        try:
            # Поиск уже ранее сохраненых
            message = cls.objects.get(message_id=headers['message-id'])
        except ObjectDoesNotExist:
            # Создание нового сообщения если не найдено
            if get_user_model().objects.filter(email=headers['to']).exists():
                # Если пользователь создан
                to = get_user_model().objects.get(email=headers['to'])
                message = cls(message_id=headers['message-id'], to=to, subject=headers['subject'],
                              url=storage['url'], key=storage['key'])
                message.save()
        return message

    def __str__(self):
        return self.message_id


class MessageHistory(models.Model):
    """
    Модель статуса письма
    """

    ACCEPTED = 'accepted'
    FAILED = 'failed'
    REJECTED = 'rejected'
    DELIVERED = 'delivered'
    COMPLAINED = 'complained'
    STORED = 'stored'

    MESSAGE_EVENTS = ((ACCEPTED, 'Принято'), (FAILED, 'Неудачно'), (REJECTED, 'Отклонено'), (DELIVERED, 'Доставлено'),
                      (COMPLAINED, 'Спам'), (STORED, 'Входящее'))

    INFO = 'info'
    WARM = 'warm'
    ERROR = 'error'

    LOG_LEVEL_CHOICES = ((INFO, 'green'), (WARM, 'yellow'), (ERROR, 'red'))

    message = models.ForeignKey(Message, verbose_name='Письмо')
    time = models.DateTimeField('Дата события')
    event = models.CharField('Событие', max_length=20, choices=MESSAGE_EVENTS)
    event_id = models.CharField('ID события', max_length=30, unique=True)
    failed_status = models.CharField('Статус неудачного', max_length=50, blank=True, null=True)
    log_level = models.CharField('Уровень лога', max_length=5, choices=LOG_LEVEL_CHOICES)
    delivery_code = models.IntegerField('Код доставки', blank=True, null=True)
    delivery_message = models.CharField('Сообщение доставки', max_length=250, blank=True, null=True)

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        ordering = ('-time', '-event')

    def get_color_event(self):
        """
        :return: статус
        """
        return '<font color="{}">'.format(self.get_log_level_display()) + self.get_event_display() + '</font>'

    get_color_event.short_description = 'Событие'
    get_color_event.allow_tags = True

    @classmethod
    def add_new_log(cls, message, item):
        """
        Добавление нового статуса письму
        """
        if not message.messagehistory_set.filter(event_id=item['id']).exists():
            # Если записи о событии нет
            mess_log = cls(message=message, event=item['event'], event_id=item['id'], log_level=item['log-level'])
            if mess_log.event == cls.FAILED:
                # Статус сообщения FAILED
                mess_log.failed_status = item['reason']
            if mess_log.event == cls.FAILED or mess_log.event == cls.DELIVERED:
                # Статус сообщения FAILED или DELIVERED
                delivery = item['delivery-status']
                mess_log.delivery_code = delivery['code']
                mess_log.delivery_message = delivery['description']
            # Сохранение времени события
            current_tz = timezone.get_current_timezone()
            mess_log.time = datetime.fromtimestamp(int(item['timestamp']), current_tz)
            mess_log.save()

    def __str__(self):
        return self.event_id


class UserProfile(models.Model):
    """
    Модель профиля пользователя
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name='Пользователь')
    fake = models.BooleanField('Некорректная почта', default=False)
    reason = models.CharField('Причина', max_length=250, blank=True, null=True)

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    @classmethod
    def set_fake_status(cls, user, reason):
        """
        Установка статуса fake
        :param user: пользователь из письма
        :param reason: причина
        """
        if cls.objects.filter(user=user).exists():
            profile = cls.objects.get(user=user)
        else:
            profile = cls(user=user)
        profile.fake, profile.reason = True, reason
        profile.save()

    def __str__(self):
        return self.user.email
