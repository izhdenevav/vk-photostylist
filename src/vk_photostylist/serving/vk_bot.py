import io
import logging
import os

import requests
import vk_api
from dotenv import load_dotenv
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from vk_api.upload import VkUpload
from vk_api.utils import get_random_id

from vk_photostylist.serving.styles import StyleError, apply_style, choose_style

load_dotenv()

VK_TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

logger = logging.getLogger(__name__)

# event
# <<class 'vk_api.bot_longpoll.VkBotMessageEvent'>
# ({'group_id': 241659236, 'type': 'message_new',
# 'event_id': '5dc45851882a0354db03c8bc5740477f3719b69e', 'v': '5.199',
# 'object': {'client_info': {'button_actions':
# ['text', 'vkpay', 'open_app', 'location', 'open_link',
# 'open_photo', 'callback', 'intent_subscribe', 'intent_unsubscribe'],
# 'keyboard': True, 'inline_keyboard': True,
# 'carousel': True, 'lang_id': 0},
# 'message': {'date': 1790052840, 'from_id': 677866122,
# 'id': 6, 'version': 10000009, 'out': 0,
# 'fwd_messages': [], 'important': False,
# 'is_hidden': False, 'attachments': [],
# 'conversation_message_id': 6, 'text': 'fffff',
# 'peer_id': 677866122, 'random_id': 0}}})>


def choose_max_size_url_photo(data: dict) -> str:
    sizes = data.get("sizes", [])

    if not sizes:
        return None

    max_size = max(sizes, key=lambda s: s.get("width", 0) * s.get("height", 0))
    return max_size.get("url", None)


def extract_photo_urls(message: dict) -> list[str]:
    photo_urls = []
    for attachment in message.get("attachments", []):
        if attachment.get("type") == "photo":
            url = choose_max_size_url_photo(attachment["photo"])
            if url:
                photo_urls.append(url)
    return photo_urls


def download_photo(url: str) -> bytes:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.content


def process_image(image: bytes, text: str) -> bytes:
    # чото вроде обработки будет
    return image


def send_reply(
    vk_session: vk_api.VkApi,
    user_id: int,
    text: str,
    images: list[bytes] | None = None,
) -> None:
    vk = vk_session.get_api()

    attachments = []
    if images:
        upload = VkUpload(vk_session)
        for i, data in enumerate(images):
            buf = io.BytesIO(data)
            buf.name = f"photo_{i}.jpg"
            photo = upload.photo_messages(photos=buf)[0]
            attachments.append(f"photo{photo['owner_id']}_{photo['id']}")

    vk.messages.send(
        user_id=user_id,
        message=text,
        attachment=",".join(attachments) if attachments else None,
        random_id=get_random_id(),
    )


def handle_message(vk_session: vk_api.VkApi, message: dict) -> None:
    user_id = message["from_id"]
    text = message.get("text", "")

    photo_urls = extract_photo_urls(message)
    if not photo_urls:
        send_reply(vk_session, user_id, "Пришлите фото с описанием обработки")
        return

    try:
        style = choose_style(text)
    except StyleError as e:
        send_reply(vk_session, user_id, str(e))
        return

    try:
        results = []
        for url in photo_urls:
            image = download_photo(url)
            results.append(apply_style(image, style))
    except StyleError as e:
        send_reply(vk_session, user_id, str(e))
        return

    send_reply(vk_session, user_id, f"Стиль: {style}", results)


def run_bot(vk_token: str, group_id: str) -> None:
    vk_session = vk_api.VkApi(token=vk_token)
    longpoll = VkBotLongPoll(vk_session, group_id)
    logger.info("Бот запущен")

    for event in longpoll.listen():
        if event.type != VkBotEventType.MESSAGE_NEW:
            continue

        message = event.object.message
        try:
            handle_message(vk_session, message)
        except Exception:
            logger.exception("Не удалось обработать сообщение")
            try:
                send_reply(
                    vk_session,
                    message["from_id"],
                    "Что-то пошло не так, попробуйте ещё раз",
                )
            except Exception:
                logger.exception("Не удалось отправить сообщение об ошибке")


if __name__ == "__main__":
    run_bot(VK_TOKEN, GROUP_ID)
