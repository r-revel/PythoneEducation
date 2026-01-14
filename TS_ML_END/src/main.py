import asyncio
import argparse
from router.router import Router
from view.telegram import TelegramClient
from controllers.app_context import AppContext
from controllers.stock_controller import StockController


async def run_bot(token: str):
    """Запускает бота с определёнными правами."""
    tg_client = TelegramClient(token)

    ctx = AppContext(tg_client)
    stock_controller = StockController(ctx)

    router = Router()

    router.route("/", stock_controller.menu)
    router.route("/forecast", stock_controller.start_forecast)
    router.route("/forecast/process", stock_controller.process_forecast)
    router.route("/stats", stock_controller.show_stats)
    router.route("/help", stock_controller.show_help)

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
