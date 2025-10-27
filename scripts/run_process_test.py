import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.absolute()
sys.path.append(str(project_root))

from app.api.process_messages import process_messages, MessagesPayload, ChatMessage

async def run():
    payload = MessagesPayload(
        userId='test-user-123',
        messages=[
            ChatMessage(role='user', message='Oi, preciso de ajuda com minha dieta considerando que tenho pressão alta', chatId='chat-1'),
            ChatMessage(role='assistant', message='Claro! Vou analisar seu perfil e histórico médico para sugerir uma dieta adequada.', chatId='chat-1')
        ]
    )
    res = await process_messages(payload, summary_only=True)
    print('Handler returned:')
    print(res)

if __name__ == '__main__':
    asyncio.run(run())
