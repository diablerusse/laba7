import json
import random
import smtplib
import socket
import threading
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


class MailServer:
    def __init__(self) -> None:
        self.cfg = Config()
        self.host = self.cfg.get('HOST', '127.0.0.1')
        self.port = int(self.cfg.get('PORT', 50007))
        self.smtp_host = self.cfg.get('SMTP_HOST')
        self.smtp_port = int(self.cfg.get('SMTP_PORT', 587))
        self.email_login = self.cfg.get('EMAIL_LOGIN')
        self.email_password = self.cfg.get('EMAIL_PASSWORD')

        if not self.email_login or not self.email_password:
            print('Warning: EMAIL_LOGIN or EMAIL_PASSWORD not found in .env')

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        print(f'Server started on {self.host}:{self.port}')
        print(f'SMTP Config: {self.smtp_host}:{self.smtp_port} as {self.email_login}')

    def start(self) -> None:
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                print(f'Connection from {addr}')
                thread = threading.Thread(
                    target=self.handle_client, args=(client_socket,)
                )
                thread.start()
        except KeyboardInterrupt:
            print('\nStopping server by user request (Ctrl+C)...')
        finally:
            self.server_socket.close()
            print('Server socket closed.')

    def handle_client(self, client_socket: Any) -> None:
        try:
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                return

            request = json.loads(data)
            user_email: str = request.get('email')
            message_text: str = request.get('text')
            validation_error = self.validate_input(user_email, message_text)

            if validation_error:
                response = {'status': 'ERROR', 'message': validation_error}
            else:
                send_result = self.send_email(user_email, message_text)
                if send_result == 'OK':
                    response = {'status': 'OK'}
                else:
                    response = {'status': 'ERROR', 'message': send_result}

            client_socket.sendall(json.dumps(response).encode('utf-8'))

        except Exception as e:
            print(f'Error handling client: {e}')
        finally:
            client_socket.close()

    def validate_input(self, email: str, text: str) -> str | None:
        if not email or '@' not in email or '.' not in email:
            return 'Invalid email address format.'
        if not text or len(text.strip()) == 0:
            return 'Message text cannot be empty.'
        return None

    def send_email(self, user_email: str, text: str) -> str:
        ticket_id = random.randint(10000, 99999)
        subject = f'[Ticket #{ticket_id}] Mailer'
        email_content = f'From: {self.email_login}\r\nTo: {user_email}\r\nSubject: {subject}\r\n\r\n{text}'

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as smtp:
                smtp.starttls()
                smtp.login(self.email_login, self.email_password)
                smtp.sendmail(
                    self.email_login, user_email, email_content.encode('utf-8')
                )

            print(f'Sent email to {user_email} with Subject: {subject}')
            return 'OK'
        except Exception as e:
            print(f'SMTP Error: {e}')
            return f'Failed to send email: {str(e)}'


if __name__ == '__main__':
    server = MailServer()
    server.start()
