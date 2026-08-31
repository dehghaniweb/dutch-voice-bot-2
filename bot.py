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
    "colette": (
        "Colette",
        "nl-NL-ColetteNeural"
    ),

    "fenna": (
        "Fenna",
        "nl-NL-FennaNeural"
    ),

    "maarten": (
        "Maarten",
        "nl-NL-MaartenNeural"
    ),
}


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    keyboard = [

        [
            InlineKeyboardButton(
                "👩 Colette",
                callback_data="voice_colette"
            )
        ],

        [
            InlineKeyboardButton(
                "👩 Fenna",
                callback_data="voice_fenna"
            )
        ],

        [
            InlineKeyboardButton(
                "👨 Maarten",
                callback_data="voice_maarten"
            )
        ]

    ]

    await update.message.reply_text(

        "🇳🇱 Dutch Voice Bot\n\n"
        "🎙 گوینده موردنظر را انتخاب کن:",

        reply_markup=
        InlineKeyboardMarkup(
            keyboard
        )
    )


async def voice_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    key = query.data.replace(
        "voice_",
        ""
    )

    if key not in VOICES:
        return

    voice_name, voice_value = VOICES[key]

    context.user_data[
        "voice"
    ] = {
        "name": voice_name,
        "value": voice_value
    }

    await query.edit_message_text(

        "✅ Voice انتخاب شد:\n\n"
        "🎙 " + voice_name +
        "\n\n"
        "حالا متن هلندی را بفرست."

    )


async def generate_voice(
    text,
    voice_value
):

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True,

            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ]
        )

        page = await browser.new_page(
            accept_downloads=True
        )

        try:

            print(
                "Opening VoiceLime..."
            )

            await page.goto(

                VOICE_URL,

                wait_until=
                "domcontentloaded",

                timeout=60000
            )

            # Cookie

            accept = page.get_by_role(
                "button",
                name="Accept All"
            )

            if await accept.count() > 0:

                try:

                    await accept.click(
                        timeout=3000
                    )

                except Exception:
                    pass

            await page.wait_for_timeout(
                2000
            )

            # Language

            language = page.locator(
                "#languageSelect"
            )

            await language.select_option(
                "nl-NL"
            )

            await page.wait_for_timeout(
                2000
            )

            # Voice

            voice_select = page.locator(
                "#voiceSelect"
            )

            await voice_select.select_option(
                voice_value
            )

            await page.wait_for_timeout(
                1000
            )

            # Text

            textarea = page.locator(
                "textarea"
            ).first

            await textarea.fill(
                text
            )

            await page.wait_for_timeout(
                500
            )

            # Generate

            generate_button = (
                page.get_by_role(
                    "button",
                    name="Generate Voice"
                )
            )

            await generate_button.click()

            print(
                "Generating..."
            )

            await page.wait_for_timeout(
                10000
            )

            # Download

            download_button = (
                page.get_by_role(
                    "button",
                    name="⬇ Download MP3"
                )
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

            file_path = (
                "/tmp/dutch_voice.mp3"
            )

            await download.save_as(
                file_path
            )

            print(
                "Audio saved."
            )

            return file_path

        finally:

            await browser.close()


async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        update.message.text or ""
    ).strip()

    if not text:
        return

    if len(text) > 5000:

        await update.message.reply_text(

            "⚠️ متن شما بیشتر از "
            "5000 کاراکتر است.\n\n"
            "لطفاً متن کوتاه‌تری بفرست."

        )

        return

    voice = context.user_data.get(
        "voice"
    )

    if not voice:

        await update.message.reply_text(

            "⚠️ ابتدا /start را بزن "
            "و Voice را انتخاب کن."

        )

        return

    await update.message.reply_text(

        "🎙 در حال ساخت فایل صوتی...\n\n"
        "🇳🇱 Voice: " +
        voice["name"]

    )

    file_path = None

    try:

        file_path = await generate_voice(

            text,

            voice["value"]

        )

        with open(
            file_path,
            "rb"
        ) as audio_file:

            await update.message.reply_audio(

                audio=audio_file,

                filename=
                "dutch_voice.mp3",

                caption=(

                    "🇳🇱 Dutch Voice\n"
                    "🎙 " +
                    voice["name"]

                )

            )

        await update.message.reply_text(

            "✅ فایل صوتی آماده شد."

        )

    except Exception as e:

        print(
            "GENERATION ERROR:",
            repr(e)
        )

        await update.message.reply_text(

            "❌ خطا هنگام ساخت فایل صوتی:\n\n"
            + str(e)[:1500]

        )

    finally:

        if (
            file_path
            and os.path.exists(file_path)
        ):

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
        CallbackQueryHandler(
            voice_selected,
            pattern="^voice_"
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT &
            ~filters.COMMAND,
            text_handler
        )
    )

    print(
        "🇳🇱 Dutch Voice Bot is running..."
    )

    app.run_polling()


if __name__ == "__main__":
    main()
