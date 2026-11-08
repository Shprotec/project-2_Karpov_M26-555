"""Разбор команд CRUD и значений в кавычках."""

import json
import shlex

from primitive_db.constants import (
    BOOL_FALSE,
    BOOL_TRUE,
    CMD_DELETE,
    CMD_INSERT,
    CMD_SELECT,
    CMD_UPDATE,
    KW_AND,
    KW_FROM,
    KW_INTO,
    KW_SET,
    KW_VALUES,
    KW_WHERE,
    VALUES_SEPARATOR,
)

QUOTES = "\"'"
PUNCTUATION = ",=()"

# столбец, =, значение и разделитель между условиями
CONDITION_SIZE = 3
CONDITION_STEP = CONDITION_SIZE + 1


def read_head(user_input, size):
    """Возвращает первые size слов и остаток строки."""
    lexer = shlex.shlex(user_input, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    words = [lexer.get_token() or "" for _ in range(size)]
    return words, lexer.instream.read().strip()


def find_quoted_end(text, start):
    """Ищет конец строки в кавычках."""
    quote = text[start]
    position = start + 1
    while position < len(text):
        if text[position] == quote:
            return position + 1
        position += 2 if text[position] == "\\" else 1
    raise ValueError(f"{text[start:]} (не закрыта кавычка)")


def tokenize(text):
    """Делит текст на строки в кавычках, знаки и слова."""
    tokens = []
    position = 0
    while position < len(text):
        char = text[position]
        if char.isspace():
            position += 1
            continue

        start = position
        if char in QUOTES:
            position = find_quoted_end(text, start)
        elif char in PUNCTUATION:
            position += 1
        else:
            while (
                position < len(text)
                and not text[position].isspace()
                and text[position] not in PUNCTUATION + QUOTES
            ):
                position += 1
        tokens.append(text[start:position])
    return tokens


def parse_literal(token):
    """Превращает токен в str, bool или int."""
    if token.startswith('"'):
        return json.loads(token)
    if token.startswith("'"):
        return token[1:-1].replace("\\'", "'").replace("\\\\", "\\")

    word = token.lower()
    if word in {BOOL_TRUE, BOOL_FALSE}:
        return word == BOOL_TRUE
    try:
        return int(token)
    except ValueError:
        raise ValueError(f"{token} (строки нужно брать в кавычки)") from None


def parse_assignments(tokens, separator):
    """Разбирает условия вида столбец = значение в словарь."""
    text = " ".join(tokens) or "пустое условие"
    if len(tokens) % CONDITION_STEP != CONDITION_SIZE:
        raise ValueError(f"{text} (ожидается столбец = значение)")

    assignments = {}
    for index in range(0, len(tokens), CONDITION_STEP):
        name, equals, token = tokens[index : index + CONDITION_SIZE]
        if index and tokens[index - 1].lower() != separator:
            raise ValueError(f"{text} (условия разделяются через {separator})")
        if equals != "=" or not name.isidentifier():
            raise ValueError(f"{text} (ожидается столбец = значение)")
        if name in assignments:
            raise ValueError(f"{name} (столбец указан дважды)")
        assignments[name] = parse_literal(token)
    return assignments


def parse_where_clause(text):
    """Разбирает условие WHERE."""
    return parse_assignments(tokenize(text), KW_AND)


def parse_set_clause(tokens):
    """Разбирает SET."""
    return parse_assignments(tokens, VALUES_SEPARATOR)


def parse_insert(user_input):
    """Возвращает имя таблицы и список значений для INSERT."""
    (command, into, table_name, keyword), tail = read_head(user_input, 4)
    if (
        command.lower() != CMD_INSERT
        or into.lower() != KW_INTO
        or not table_name
        or keyword.lower() != KW_VALUES
        or not tail.startswith("(")
        or not tail.endswith(")")
    ):
        raise ValueError(
            f'{user_input.strip()} (пример: insert into users values ("Анна", 28))'
        )

    tokens = tokenize(tail[1:-1])
    separators = tokens[1::2]
    if not tokens or len(tokens) % 2 == 0 or set(separators) - {VALUES_SEPARATOR}:
        raise ValueError(f"{tail} (значения разделяются запятыми)")
    return table_name, [parse_literal(token) for token in tokens[::2]]


def parse_select(user_input):
    """Возвращает имя таблицы и необязательное условие WHERE."""
    (command, source, table_name), tail = read_head(user_input, 3)
    if source == "*" and table_name.lower() == KW_FROM:
        (table_name,), tail = read_head(tail, 1)
        source = KW_FROM
    if command.lower() != CMD_SELECT or source.lower() != KW_FROM or not table_name:
        raise ValueError(f"{user_input.strip()} (пример: select from users)")
    if not tail:
        return table_name, None

    (keyword,), conditions = read_head(tail, 1)
    if keyword.lower() != KW_WHERE:
        raise ValueError(f"{keyword} (после имени таблицы ожидается where)")
    return table_name, parse_where_clause(conditions)


def parse_update(user_input):
    """Возвращает имя таблицы, новые значения и условие WHERE."""
    (command, table_name, keyword), tail = read_head(user_input, 3)
    if command.lower() != CMD_UPDATE or not table_name or keyword.lower() != KW_SET:
        raise ValueError(
            f"{user_input.strip()} "
            '(пример: update users set name = "Анна" where ID = 1)'
        )

    tokens = tokenize(tail)
    where_index = next(
        (
            index
            for index in range(CONDITION_SIZE, len(tokens), CONDITION_STEP)
            if tokens[index].lower() == KW_WHERE
        ),
        None,
    )
    if where_index is None:
        raise ValueError(f"{user_input.strip()} (для update нужно условие where)")

    changes = parse_set_clause(tokens[:where_index])
    conditions = parse_assignments(tokens[where_index + 1 :], KW_AND)
    return table_name, changes, conditions


def parse_delete(user_input):
    """Возвращает имя таблицы и обязательное условие WHERE."""
    (command, source, table_name, keyword), tail = read_head(user_input, 4)
    if (
        command.lower() != CMD_DELETE
        or source.lower() != KW_FROM
        or not table_name
        or keyword.lower() != KW_WHERE
    ):
        raise ValueError(
            f"{user_input.strip()} (пример: delete from users where ID = 1)"
        )
    return table_name, parse_where_clause(tail)
