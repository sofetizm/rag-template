from __future__ import annotations

import re
from functools import lru_cache

import snowballstemmer

_WORD = re.compile(r"\w+", re.UNICODE)
_CYRILLIC = re.compile(r"[а-я]")

STOPWORDS = frozenset(
    """
    и в во не что он на я с со как а то все она так его но да ты к у же вы за бы по только ее мне было
    вот от меня еще нет о из ему теперь когда даже ну вдруг ли если уже или ни быть был него до вас нибудь
    опять уж вам ведь там потом себя ничего ей может они тут где есть надо ней для мы тебя их чем была сам
    чтоб без будто чего раз тоже себе под будет ж тогда кто этот того потому этого какой совсем ним здесь
    этом один почти мой тем чтобы нее сейчас были куда зачем всех никогда можно при наконец два об другой
    хоть после над больше тот через эти нас про всего них какая много разве три эту моя впрочем хорошо
    свою этой перед иногда лучше чуть том нельзя такой им более всегда конечно всю между это также который
    которые которая которого если
    a an and are as at be but by for if in into is it no not of on or such that the their then there these
    they this to was will with what which who whom how do does did can could should would i you we he she
    me my our your its from have has had been being so than too very just about
    """.split()
)


@lru_cache(maxsize=2)
def _stemmer(lang: str):
    return snowballstemmer.stemmer(lang)


@lru_cache(maxsize=200_000)
def stem(word: str) -> str:
    lang = "russian" if _CYRILLIC.search(word) else "english"
    return _stemmer(lang).stemWord(word)


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in _WORD.findall(text.lower().replace("ё", "е")):
        parts = [raw] + ([p for p in raw.split("_") if p] if "_" in raw.strip("_") else [])
        for word in parts:
            if word in STOPWORDS or (len(word) == 1 and not word.isdigit()):
                continue
            tokens.append(stem(word))
    return tokens
