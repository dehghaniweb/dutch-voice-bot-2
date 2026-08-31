import os
import time

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from playwright.async_api import async_playwright


TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN"
)

VOICE_URL = (
    "https://voicelime.com/voice-generator"
)


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


SPEEDS = {

    "slow": (
        "🐢 کمی کم",
        -10
    ),

    "normal": (
        "🎙 متوسط",
        0
    ),

    "fast": (
        "⚡ کمی زیاد",
        10
    ),
}


# =================================
# START
# =================================

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


# =================================
# VOICE
# =================================

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

    context.user_data["voice"] = {
        "name": voice_name,
        "value": voice_value
    }

    keyboard = [

        [
            InlineKeyboardButton(
                "🐢 کمی کم",
                callback_data="speed_slow"
            )
        ],

        [
            InlineKeyboardButton(
                "🎙 متوسط",
                callback_data="speed_normal"
            )
        ],

        [
            InlineKeyboardButton(
                "⚡ کمی زیاد",
                callback_data="speed_fast"
            )
        ]

    ]

    await query.edit_message_text(

        "🎙 Voice:\n"
        + voice_name
        + "\n\n"
        "⚡ سرعت را انتخاب کن:",

        reply_markup=
        InlineKeyboardMarkup(
            keyboard
        )
    )


# =================================
# SPEED
# =================================

async def speed_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    key = query.data.replace(
        "speed_",
        ""
    )

    if key not in SPEEDS:
        return

    voice = context.user_data.get(
        "voice"
    )

    if not voice:

        await query.edit_message_text(
            "⚠️ ابتدا Voice را انتخاب کن."
        )

        return

    speed_name, speed_value = SPEEDS[key]

    context.user_data["speed"] = {
        "name": speed_name,
        "value": speed_value
    }

    await query.edit_message_text(

        "✅ تنظیمات آماده است.\n\n"

        "🎙 Voice: " +
        voice["name"] +

        "\n⚡ Speed: " +
        speed_name +

        "\n\n"

        "🇳🇱 حالا فقط متن هلندی را بفرست."

    )


# =================================
# GENERATE VOICE
# =================================

async def generate_voice(
    text,
    voice_value,
    speed_value
):

    filename = (
        "/tmp/dutch_voice_" +
        str(int(time.time())) +
        ".mp3"
    )

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

            await page.wait_for_timeout(
                3000
            )

            # -------------------------
            # COOKIE
            # -------------------------

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

            # -------------------------
            # LANGUAGE
            # -------------------------

            language = page.locator(
                "#languageSelect"
            )

            await language.select_option(
                "nl-NL"
            )

            await page.wait_for_timeout(
                2000
            )

            # -------------------------
            # VOICE
            # -------------------------

            voice_select = page.locator(
                "#voiceSelect"
            )

            await voice_select.select_option(
                voice_value
            )

            await page.wait_for_timeout(
                1000
            )

            # -------------------------
            # TEXT
            # -------------------------

            textarea = page.locator(
                "textarea"
            ).first

            await textarea.fill(
                text
            )

            # اطمینان از اینکه فقط متن ماست
            actual_text = await textarea.input_value()

            print(
                "TEXT SENT:",
                actual_text
            )

            # -------------------------
            # SPEED
            # -------------------------

            ranges = page.locator(
                'input[type="range"]'
            )

            range_count = await ranges.count()

            print(
                "Range inputs:",
                range_count
            )

            if range_count >= 2:

                speed = ranges.nth(1)

                await speed.evaluate(

                    """
                    (element, value) => {

                        element.value = value;

                        element.dispatchEvent(
                            new Event(
                                'input',
                                {bubbles: true}
                            )
                        );

                        element.dispatchEvent(
                            new Event(
                                'change',
                                {bubbles: true}
                            )
                        );

                    }
                    """,

                    str(speed_value)

                )

                print(
                    "Speed:",
                    speed_value
                )

            # -------------------------
            # GENERATE
            # -------------------------

            generate_button = (
                page.get_by_role(
                    "button",
                    name="Generate Voice"
                )
            )

            await generate_button.wait_for(
                state="visible",
                timeout=30000
            )

            print(
                "Generating..."
            )

            await generate_button.click()

            # -------------------------
            # WAIT
            # -------------------------

            await page.wait_for_timeout(
                10000
            )

            # -------------------------
            # DOWNLOAD
            # -------------------------

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
                timeout=60000
            ) as info:

                await download_button.click()

            download = await info.value

            await download.save_as(
                filename
            )

            print(
                "Saved:",
                filename
            )

            return filename

        finally:

            await browser.close()


# =================================
# TEXT
# =================================

async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        update.message.text or ""
    ).strip()

    if not text:
        return

    # جلوگیری از تبدیل دستورات به صدا
    if text.startswith("/"):
        return

    if len(text) > 5000:

        await update.message.reply_text(

            "⚠️ متن بیشتر از "
            "5000 کاراکتر است."

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

    speed = context.user_data.get(
        "speed"
    )

    if not speed:

        await update.message.reply_text(

            "⚠️ ابتدا Speed را انتخاب کن."

        )

        return

    await update.message.reply_text(

        "🎙 در حال ساخت فایل صوتی...\n\n"

        "🇳🇱 Voice: " +
        voice["name"] +

        "\n⚡ Speed: " +
        speed["name"]

    )

    file_path = None

    try:

        file_path = await generate_voice(

            text,

            voice["value"],

            speed["value"]

        )

        with open(
            file_path,
            "rb"
        ) as audio:

            await update.message.reply_audio(

                audio=audio,

                filename=
                "dutch_voice.mp3",

                caption=(

                    "🇳🇱 Dutch Voice\n"
                    "🎙 " +
                    voice["name"] +
                    "\n⚡ " +
                    speed["name"]

                )

            )

        print(
            "Audio sent."
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

                os.remove(
                    file_path
                )

            except Exception:
                pass


# =================================
# MAIN
# =================================

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
        CallbackQueryHandler(
            speed_selected,
            pattern="^speed_"
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
