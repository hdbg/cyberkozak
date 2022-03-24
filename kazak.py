from pyrogram import Client
from pyrogram.types import Message

from pyrogram.raw import functions, types
from pyrogram.errors.exceptions import bad_request_400

import structlog
import re

app_id = int(input("Введіть app_id отриманний від телеграму:"))
app_hash = шnput("Введіть app_hash отриманний від телеграму:")

bot_url = "@CyberArm_bot"

logger = structlog.get_logger("Cyber Kozak")


class CyberKozak:
    client: Client

    panel: Message

    def __init__(self):
        logger.info("козак прокинувся")
        self.client = Client("kozak", app_id, app_hash)

        self.client.start()

        self.bot_chat = self.client.get_chat(bot_url)

        self.client.send_message(bot_url, text="/start")
        self.wait_for("Ласкаво просимо").click(0)

        self.panel = self.wait_for("Завдання")

    def last(self):
        return self.client.get_history(bot_url, limit=1)[0]

    def wait_for(self, content):
        while True:
            if content in (msg := self.last()).text:
                return msg

    def update(self):
        self.panel = self.client.get_messages(bot_url, self.panel.message_id)

    def report_post(self, p):
        link = p.reply_markup.inline_keyboard[0][0]["url"]

        match = re.match(r"https:\/\/t.me\/(.+)\/(\d+)", link)

        if match is None:
            p.click(2)
            logger.warning("не розумію що написано", link=link)
            return False

        uname, msg_id = match.group(1), int(match.group(2))

        evil_channel = self.client.join_chat(uname)
        target = self.client.get_messages(evil_channel.id, msg_id)

        report_reason = types.InputReportReasonViolence(
        ) if "насильство" in p.text else types.InputReportReasonSpam()

        result = self.client.send(functions.messages.Report(
            peer=self.client.resolve_peer(evil_channel.id), id=[target.message_id],
            reason=report_reason, message=""))

        evil_channel.leave()

        return result, evil_channel.title

    def report_channel(self, p):
        link = p.reply_markup.inline_keyboard[0][0]["url"]

        print(link[len("https://t.me/"):])

        evil_channel = self.client.join_chat(link[len("https://t.me/"):])

        report_reason = types.InputReportReasonViolence(
        ) if "насильство" in p.text else types.InputReportReasonSpam()

        result = self.client.send(functions.account.ReportPeer(
            peer=self.client.resolve_peer(evil_channel.id),
            reason=report_reason, message=""))

        evil_channel.leave()

        return result, evil_channel.title

    def main_loop(self):
        while 1:
            self.update()
            p = self.panel

            # skip if not telegram task
            if "t.me" not in p.text:
                try:
                    p.click(2)
                except bad_request_400.DataInvalid:
                    pass

                logger.warning("пропускаю, не телеграм", id=p.message_id)
                continue
            try:
                type_table = {"пост": self.report_post,
                            "канал": self.report_channel}

                result, title = None, None

                for k, v in type_table.items():
                    if k in p.text:
                        logger.info("працюю", type=k)
                        result, title = v(p)

                if result:
                    logger.info("кацапчик у репорті", channel=title)
                    try:
                        p.click(1)
                    except bad_request_400.DataInvalid:
                        pass
                else:
                    logger.error("кацапчик не піддався", channel=title)
                    # logger.debug("деталі", msg=p.text)
                    try:
                        p.click(2)
                    except bad_request_400.DataInvalid:
                        pass
            except Exception:
                logger.exception("щось спина зажурилась...")

    def __del__(self):
        self.client.stop()


if __name__ == "__main__":
    i = CyberKozak()
    i.main_loop()
