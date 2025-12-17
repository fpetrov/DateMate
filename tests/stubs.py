from datetime import datetime, timezone
from types import SimpleNamespace

from aiogram.exceptions import TelegramBadRequest


class DummyFSM:
    def __init__(self):
        self.data = {}
        self.state = None

    async def get_data(self):
        return dict(self.data)

    async def update_data(self, data=None, **kwargs):
        payload = data or {}
        payload.update(kwargs)
        self.data.update(payload)

    async def set_data(self, data):
        self.data = dict(data)

    async def set_state(self, state):
        self.state = state


class FakeMessage:
    def __init__(self, chat_id: int, message_id: int = 1, text: str | None = None, from_user_id: int | None = None, photo=None, date=None):
        self.chat = SimpleNamespace(id=chat_id)
        self.message_id = message_id
        self.date = date or datetime.now(timezone.utc)
        self.from_user = SimpleNamespace(id=from_user_id or chat_id + 1, username="user")
        self.text = text
        self.photo = photo or []


class FakeCallback:
    def __init__(self, data: str, message: FakeMessage, from_user_id: int | None = None):
        self.data = data
        self.message = message
        self.from_user = SimpleNamespace(id=from_user_id or message.from_user.id, username="user")
        self._answered = False
        self.chat = message.chat
        self.message_id = message.message_id
        self.date = message.date

    async def answer(self, *args, **kwargs):
        self._answered = True


class DummyBot:
    def __init__(self):
        self.sent_messages = []
        self.edited_messages = []
        self.sent_photos = []
        self.deleted_messages = []
        self.get_chat_calls = []
        self.edit_error: Exception | None = None
        self.edit_media_error: Exception | None = None
        self.chat_usernames: dict[int, str] = {}

    async def send_message(self, chat_id, text, **kwargs):
        self.sent_messages.append((chat_id, text))
        return FakeMessage(chat_id, len(self.sent_messages), text)

    async def edit_message_text(self, chat_id, message_id, text, **kwargs):
        if self.edit_error:
            raise self.edit_error
        self.edited_messages.append((chat_id, message_id, text))

    async def send_photo(self, chat_id, photo, caption=None, **kwargs):
        self.sent_photos.append((chat_id, photo, caption))
        return FakeMessage(chat_id, len(self.sent_photos) + 100, caption)

    async def edit_message_media(self, chat_id, message_id, media, **kwargs):
        if self.edit_media_error:
            raise self.edit_media_error
        self.edited_messages.append((chat_id, message_id, media))

    async def delete_message(self, chat_id, message_id):
        self.deleted_messages.append((chat_id, message_id))

    async def get_chat(self, telegram_id: int):
        self.get_chat_calls.append(telegram_id)
        if telegram_id in self.chat_usernames:
            return SimpleNamespace(username=self.chat_usernames[telegram_id])
        raise TelegramBadRequest(message="not found", method="get_chat")
