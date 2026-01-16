import datetime as dt
import email
import imaplib
import re
import time
from email.header import Header, decode_header
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any


class Config:
    def __init__(self, env_file: str = '.env') -> None:
        self.config = {}
        path = Path(env_file)

        if path.exists():
            with path.open('r', encoding='utf-8') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        self.config[key.strip()] = value.strip()

    def get(self, key: Any, default: Any | None = None) -> Any:
        return self.config.get(key, default)


class MailCollector:
    def __init__(self) -> None:
        self.cfg = Config()
        self.email_login = self.cfg.get('EMAIL_LOGIN')
        self.email_password = self.cfg.get('EMAIL_PASSWORD')

        # Читаем параметры IMAP из .env
        self.imap_host = self.cfg.get('IMAP_HOST', 'imap.gmail.com')
        # Порт обязательно преобразуем в int
        self.imap_port = int(self.cfg.get('IMAP_PORT', 993))

        # Читаем частоту проверки из .env
        self.check_interval = int(self.cfg.get('PERIOD_CHECK', 60))

        self.time_limit_minutes = 10

    def decode_mime_words(self, s: Header | str) -> str:
        if not s:
            return ''
        decoded_list = decode_header(s)
        result = []
        for content, encoding in decoded_list:
            if isinstance(content, bytes):
                if encoding:
                    try:
                        result.append(content.decode(encoding))
                    except:
                        result.append(content.decode('utf-8', 'ignore'))
                else:
                    result.append(content.decode('utf-8', 'ignore'))
            else:
                result.append(str(content))
        return ''.join(result)

    def get_email_body(self, msg: Any) -> Any:
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition'))
                if (
                    content_type == 'text/plain'
                    and 'attachment' not in content_disposition
                ):
                    return part.get_payload(decode=True).decode()
        else:
            return msg.get_payload(decode=True).decode()
        return ''

    def start(self) -> None:
        print(f'Collector started.')
        print(f'Connecting to {self.imap_host}:{self.imap_port} as {self.email_login}')
        print(f'Check interval: {self.check_interval} seconds')

        try:
            while True:
                self.check_mail()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            print('\nCollector stopped.')

    def check_mail(self) -> None:
        try:
            # Используем хост и порт из конфига
            mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            mail.login(self.email_login, self.email_password)
            mail.select('inbox')

            status, messages = mail.search(None, 'UNSEEN')

            if status != 'OK':
                return

            email_ids = messages[0].split()
            if not email_ids:
                return

            print(f'Checking {len(email_ids)} unread message(s)...')

            for e_id in email_ids:
                res, msg_data = mail.fetch(e_id, '(RFC822)')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])

                        # --- ПРОВЕРКА ВРЕМЕНИ ---
                        try:
                            msg_date_str = msg.get('Date')
                            email_date = parsedate_to_datetime(msg_date_str)
                            now = dt.datetime.now(email_date.tzinfo)

                            if now - email_date > dt.timedelta(
                                minutes=self.time_limit_minutes
                            ):
                                print(f'-> Skipping old message from {email_date}')
                                continue
                        except Exception as e:
                            print(f'Date parsing error: {e}, skipping.')
                            continue
                        # ------------------------

                        subject_raw = msg.get('Subject')
                        subject = self.decode_mime_words(subject_raw)
                        body = self.get_email_body(msg).strip()

                        print(f'-> Processing NEW email: {subject}')
                        self.process_message(subject, body)

            mail.close()
            mail.logout()

        except Exception as e:
            print(f'IMAP Error: {e}')

    def process_message(self, subject: str, text: str) -> None:
        match = re.search(r'\[Ticket #(\d+)\]', subject)
        if match:
            ticket_id = match.group(1)
            self.log_success(ticket_id, text)
        else:
            self.log_error(f'Invalid Subject: {subject} | Body: {text}')

    def log_success(self, ticket_id: str | Any, text: str) -> None:
        # Используем Path(...).open(...)
        with Path('success_request.log').open('a', encoding='utf-8') as f:
            f.write(f'{ticket_id} | {text}\n')
        print(f'   LOGGED SUCCESS: Ticket #{ticket_id}')

    def log_error(self, error_text: str) -> None:
        # Используем Path(...).open(...)
        with Path('error_request.log').open('a', encoding='utf-8') as f:
            timestamp = dt.datetime.now(dt.UTC).strftime('%Y-%m-%d %H:%M:%S')
            f.write(f'{timestamp} | {error_text}\n')
        print(f'   LOGGED ERROR: {error_text}')


if __name__ == '__main__':
    collector = MailCollector()
    collector.start()
