import textwrap

GREETINGS = textwrap.dedent("""\
    Guten Tag!
    Меня зовут Гриша. Schön, dich kennenzulernen, {name}! Присаживайся, здесь viele свободных мест.
    Давай расскажу о себе: Я живу в далекой Deutschland, наслаждаюсь пивом и отлично провожу время!
    А также подрабатываю Überbringer, так что если хочешь, буду держать тебя в курсе событий у нас тут :)
    Oh ja! Willkommen!
    P.S. Можешь узнать подробнее о моих невероятных умениях с помощью команды /hilfe
    """)

HELP = textwrap.dedent("""\
    Так приятно, что ты интересуешься моим богатым внутренним миром! Вот что я умею:
    /usage - расскажу сколько трафика использовано в текущий момент
    /stats - покажу статистику использования трафика за период, который попросишь
    /notify - подпишись на уведомления и я буду присылать тебе последние новости \U0001f609
    /threshold - настрой уведомления. На скольких процентах израсходованного трафика планируешь бегать в панике? (сейчас у тебя {threshold}%)
    Не забудь включить уведомления, чтобы я смог предупредить тебя согласно этой настройке!
    /shutup - отключи уведомления и я тебя не побеспокою
    /hilfe - всегда готов напомнить тебе о своих невероятных умениях :)
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

USAGE_NOTIFICATION = textwrap.dedent("""\
    Achtung!
    Текущее использование трафика {percent}%!
    {used} из {quota}
    """)

THRESHOLD_PROMPT = textwrap.dedent("""\
    Окей, на скольки процентах тебя уведомлять? Сейчас у тебя {current}%.
    Жду от тебя целое число от 1 до 99!
    """)

UNKNOWN_USER = [
    "Не нашел тебя в своем дневничке)",
    "Подожди секунду, а я тебя точно знаю?",
    "Подожди секунду, а мы точно знакомы?",
    "Подожди, а ты как сюда попал!?",
]

THRESHOLD_SET = textwrap.dedent("""\
    Договорились! Пришлю тебе уведомление, если использование трафика будет выше {threshold}%!
    """)

THRESHOLD_SET_WARN = textwrap.dedent("""\
    Договорились!
    Не забудь включить уведомления с помощью /notify, тогда я напишу тебе, если использование трафика будет выше {threshold}%!
    """)
