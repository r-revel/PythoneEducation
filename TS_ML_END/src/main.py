import asyncio
import argparse
from router.router import Router
from view.telegram import TelegramClient
from controller.app_context import AppContext
from controller.public_controller import PublicController

async def run_bot(token: str):
    """Запускает бота с определёнными правами."""
    tg_client = TelegramClient(token)

    ctx = AppContext(tg_client)
    public = PublicController(ctx)

    router = Router()

  
    router.route("/", public.menu)
    router.route("/price", public.menu)



    await tg_client.init(router=router)

    try:
        while True:
            await asyncio.sleep(1)
    except (asyncio.CancelledError, KeyboardInterrupt):
        await tg_client.stop()



async def main():
    parser = argparse.ArgumentParser(description="Запуск Telegram бота с разными правами.")
    parser.add_argument("--token", type=str, required=False, help="Токен бота от @BotFather")

    args = parser.parse_args()

    await run_bot(args.token)
       
if __name__ == "__main__":
    asyncio.run(main())
