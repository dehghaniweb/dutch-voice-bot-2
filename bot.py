import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from playwright.async_api import async_playwright

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

VOICE_URL = "https://voicelime.com/voice-generator"

VOICES = {
    "colette": ("Colette", "nl-NL-ColetteNeural"),
    "fenna": ("Fenna", "nl-NL-FennaNeural"),
    "maarten": ("Maarten", "nl-NL-MaartenNeural"),
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await update.message.reply_text(
        "🇳🇱 Dutch Voice Bot\n\n"
        "متن هلندی خودت را بفرست.\n\n"
        "مثال:\n"
        "De compressor werkt normaal."
    )


async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()

    if not text:
        return

    if len(text) > 5000:

        await update.message.reply_text(
            "⚠️ متن بیشتر از 5000 کاراکتر است."
        )

        return

    context.user_data["text"] = text

    keyboard = [
        [
            InlineKeyboardButton(
                "👩 Colette",
                callback_data="voice_colette"
            ),
            InlineKeyboardButton(
                "👩 Fenna",
                callback_data="voice_fenna"
            ),
        ],
        [
            InlineKeyboardButton(
                "👨 Maarten",
                callback_data="voice_maarten"
            )
        ],
    ]

    await update.message.reply_text(
        "🎙 Voice هلندی را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def voice_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    key = query.data.replace("voice_", "")

    if key not in VOICES:
        return

    voice_name, voice_value = VOICES[key]

    text = context.user_data.get("text")

    if not text:

        await query.message.reply_text(
            "⚠️ اول یک متن هلندی بفرست."
        )

        return

    await query.edit_message_text(
        f"🎙 Voice انتخاب شد:\n\n"
        f"{voice_name}\n\n"
        "⏳ در حال ساخت فایل صوتی..."
    )

    file_path = None

    try:

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

            await page.goto(
                VOICE_URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            # Cookie
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

            # Language
            language = page.locator(
                "#languageSelect"
            )

            await language.select_option(
                "nl-NL"
            )

            await page.wait_for_timeout(2000)

            # Voice
            voice_select = page.locator(
                "#voiceSelect"
            )

            await voice_select.select_option(
                voice_value
            )

            await page.wait_for_timeout(1000)

            # Text
            textarea = page.locator(
                "textarea"
            ).first

            await textarea.fill(text)

            # Generate
            generate_button = page.get_by_role(
                "button",
                name="Generate Voice"
            )

            await generate_button.click()

            await page.wait_for_timeout(
                10000
            )

            # Download
            download_button = page.get_by_role(
                "button",
                name="⬇ Download MP3"
            )

            if await download_button.count() == 0:

                raise Exception(
                    "Download MP3 button not found."
                )

            async with page.expect_download(
                timeout=30000
            ) as download_info:

                await download_button.click()

            download = await download_info.value

            file_path = "/tmp/dutch_voice.mp3"

            await download.save_as(
                file_path
            )

            await browser.close()

        # Send MP3
        with open(
            file_path,
            "rb"
        ) as audio_file:

            await query.message.reply_audio(
                audio=audio_file,
                filename="dutch_voice.mp3",
                caption=(
                    f"🇳🇱 Dutch Voice\n"
                    f"🎙 {voice_name}\n\n"
                    f"{text}"
                )
            )

        await query.message.reply_text(
            "✅ فایل صوتی آماده شد."
        )

    except Exception as e:

        print(
            "VOICE ERROR:",
            repr(e)
        )

        await query.message.reply_text(
            "❌ خطا هنگام ساخت فایل صوتی:\n\n"
            + str(e)[:1500]
        )

    finally:

        if file_path and os.path.exists(file_path):

            try:
                os.remove(file_path)
            except Exception:
                pass


def main():

    if not TOKEN:

        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing."
        )

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_text
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            voice_selected,
            pattern="^voice_"
        )
    )

    print(
        "🇳🇱 Dutch Voice Bot 2 is running..."
    )

    app.run_polling()


if __name__ == "__main__":
    main()
