import textwrap

GREETINGS = textwrap.dedent("""\
            Guten Tag!
            Меня зовут Гриша. Schön, dich kennenzulernen, {name}! Присаживайся, здесь viele свободных мест.
            Давай расскажу о себе: Я живу в далекой Deutschland, наслаждаюсь пивом и отлично провожу время!
            Я подрабатываю Überbringer, так что если хочешь, буду держать тебя в курсе событий у нас тут :)
            Oh ja! Willkommen!
            """)

CONFUSED_REPLIES = [
    textwrap.dedent(reply)
    for reply in (
        "...wut?",
        "Извини, ich verstehe das nicht :(",
        "Bitte nur auf Deutsch!",
        "О да, я люблю ПИВО!!! Извини, что ты говоришь?",
        "Не могу разобрать, die Musik ist zu laut!",
        "Oh Bier, meine Liebe..",
        "Ich verstehe kein Wort Russisch, сори",
        "Ich bin zu betrunken, lasst mich in Ruhe :)",
        "huh? ПИВОООО",
        "Großartig! Aber ich muss geschäftlich verreisen",
        "Ich muss dringend pinkeln – zu viel Bier! Oh ja!",
    )
]

BEER_REPLIES = [
    "Пиво? ПИИИВООООООО",
    "Mmm, Bier, meine Liebe!",
    "Да, больше пива!",
    "Мне грустно когда пива нет рядом :(",
    "Заглядывай к нам в таверну на кружечку Gänstaller Bräu Schwarze :)",
]

UNKNOWN_COMMAND = "Я не знаю что с этим делать :("

BOT_ERROR = [
    "Oh Mist! Ошибка!",
    "Произошел конфуз!",
    "Я СЛОМАЛСЯ! Ich bin zusammengebrochen!",
    "Нееет за чтооо! (Я очень сломан)",
    "Я сломан. Теперь только пиво может мне помочь!",
]

USAGE_REPLY = textwrap.dedent("""\
        Сейчас использовано {percent}%
        {used} из {quota}
        """)

IMAGE_REPLY = "Спасибо, повешу на стену!"
