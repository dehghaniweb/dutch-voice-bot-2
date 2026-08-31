import os
import asyncio
from pathlib import Path

from telegram import Bot
from playwright.async_api import async_playwright

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TEXT = os.getenv("VOICE_TEXT")

VOICE_URL = "https://voicelime.com/voice-generator"

VOICES = {
    "colette": "nl-NL-ColetteNeural",
    "fenna": "nl-NL-FennaNeural",
    "maarten": "nl-NL-MaartenNeural",
}


async def generate_voice(text, voice_value):

    file_path = Path("/tmp/dutch_voice.mp3")

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        page = await browser.new_page(
            accept_downloads=True
        )

        try:

            print("Opening VoiceLime...")

            await page.goto(
                VOICE_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            accept = page.get_by_role(
                "button",
                name="Accept All"
            )

            if await accept.count() > 0:
                try:
                    await accept.click(timeout=3000)
                except Exception:
                    pass

            await page.wait_for_timeout(2000)

            language = page.locator(
                "#languageSelect"
            )

            await language.select_option("nl-NL")

            await page.wait_for_timeout(2000)

            voice = page.locator(
                "#voiceSelect"
            )

            await voice.select_option(
                voice_value
            )

            textarea = page.locator(
                "textarea"
            ).first

            await textarea.fill(text)

            generate = page.get_by_role(
                "button",
                name="Generate Voice"
            )

            await generate.click()

            print("Generating voice...")

            await page.wait_for_timeout(10000)

            download_button = page.get_by_role(
                "button",
                name="⬇ Download MP3"
            )

            await download_button.wait_for(
                state="visible",
                timeout=60000
            )

            async with page.expect_download(
                timeout=30000
            ) as info:

                await download_button.click()

            download = await info.value

            await download.save_as(
                str(file_path)
            )

            print("Audio saved.")

            return file_path

        finally:

            await browser.close()


async def main():

    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing."
        )

    if not CHAT_ID:
        raise RuntimeError(
            "TELEGRAM_CHAT_ID is missing."
        )

    if not TEXT:
        raise RuntimeError(
            "VOICE_TEXT is missing."
        )

    # فعلاً Colette را به عنوان Voice پیش‌فرض استفاده می‌کنیم
    voice_value = VOICES["colette"]

    print("Text received:")
    print(TEXT)

    file_path = await generate_voice(
        TEXT,
        voice_value
    )

    bot = Bot(TOKEN)

    with open(
        file_path,
        "rb"
    ) as audio:

        await bot.send_audio(
            chat_id=CHAT_ID,
            audio=audio,
            caption="🇳🇱 Dutch Voice\n🎙 Colette"
        )

    file_path.unlink(
        missing_ok=True
    )

    print("Audio sent to Telegram.")
    print("BOT FINISHED.")


if __name__ == "__main__":
    asyncio.run(main())
