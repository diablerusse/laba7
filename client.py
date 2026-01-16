import json
import socket
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


def main() -> None:
    cfg = Config()

    host = cfg.get('HOST', '127.0.0.1')
    port = int(cfg.get('PORT', 50007))

    print('--- Mailer Client ---')
    print(f'Connecting to Server at {host}:{port}')

    while True:
        try:
            email = input('\nEnter recipient email: ').strip()
            text = input('Enter message text: ').strip()
        except KeyboardInterrupt:
            print('\nExiting client.')
            break

        if not email or not text:
            print('Error: Email and text must not be empty.')
            continue

        request_data = {'email': email, 'text': text}

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                s.sendall(json.dumps(request_data).encode('utf-8'))

                response_raw = s.recv(1024)
                if not response_raw:
                    print('Server closed connection unexpectedly.')
                    break

                response = json.loads(response_raw.decode('utf-8'))

                if response.get('status') == 'OK':
                    print('Server response: OK. Email sent successfully.')
                else:
                    error_msg = response.get('message', 'Unknown error')
                    print(f'Server error: {error_msg}')
                    print('Please try again.')

        except ConnectionRefusedError:
            print(f'Error: Could not connect to {host}:{port}. Is server running?')
            break
        except Exception as e:
            print(f'Unexpected error: {e}')
            break


if __name__ == '__main__':
    main()
