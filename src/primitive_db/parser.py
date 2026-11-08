"""Разбор команд CRUD и значений в кавычках."""

import json
import shlex

PUNCTUATION = ",=()"


def _read_head(user_input, size):
    lexer = shlex.shlex(user_input, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    words = [lexer.get_token() or "" for _ in range(size)]
    return words, lexer.instream.read().strip()


def _quoted_end(text, start):
    quote = text[start]
    position = start + 1
    while position < len(text):
        if text[position] == quote:
            return position + 1
        position += 2 if text[position] == "\\" else 1
    raise ValueError("Закрой кавычки в значении.")


def _tokenize(text):
    tokens = []
    position = 0
    while position < len(text):
        char = text[position]
        if char.isspace():
            position += 1
            continue

        start = position
        if char in "\"'":
            position = _quoted_end(text, start)
        elif char in PUNCTUATION:
            position += 1
        else:
            while (
                position < len(text)
                and not text[position].isspace()
                and text[position] not in PUNCTUATION + "\"'"
            ):
                position += 1
        tokens.append(text[start:position])
    return tokens


def _parse_literal(token):
    if token.startswith('"'):
        return json.loads(token)
    if token.startswith("'"):
        return token[1:-1].replace("\\'", "'").replace("\\\\", "\\")

    word = token.lower()
    if word in {"true", "false"}:
        return word == "true"
    try:
        return int(token)
    except ValueError:
        raise ValueError(f"Строковое значение {token} нужно взять в кавычки.") from None


def _parse_assignments(tokens, separator):
    if len(tokens) % 4 != 3:
        raise ValueError("Укажи условие в формате столбец = значение.")

    assignments = {}
    for index in range(0, len(tokens), 4):
        name, equals, token = tokens[index:index + 3]
        if name.startswith(("'", '"')):
            name = _parse_literal(name)
        if equals != "=" or not name or name in assignments:
            raise ValueError("Каждый столбец в условии должен быть указан один раз.")
        if index and tokens[index - 1].lower() != separator:
            raise ValueError(f"Разделяй условия с помощью {separator.upper()}.")
        assignments[name] = _parse_literal(token)
    return assignments


def parse_insert(user_input):
    """Возвращает имя таблицы и список значений для INSERT."""
    (command, into, table_name, keyword), tail = _read_head(user_input, 4)
    if (
        command.lower() != "insert"
        or into.lower() != "into"
        or not table_name
        or keyword.lower() != "values"
        or not tail.startswith("(")
        or not tail.endswith(")")
    ):
        raise ValueError('Пример: insert into users values ("Анна", 28)')

    tokens = _tokenize(tail[1:-1])
    if tokens and (len(tokens) % 2 == 0 or any(token != "," for token in tokens[1::2])):
        raise ValueError("Разделяй значения запятыми.")
    return table_name, [_parse_literal(token) for token in tokens[::2]]


def parse_select(user_input):
    """Возвращает имя таблицы и необязательное условие WHERE."""
    (command, source, table_name), tail = _read_head(user_input, 3)
    if source == "*" and table_name.lower() == "from":
        (table_name,), tail = _read_head(tail, 1)
        source = "from"
    if command.lower() != "select" or source.lower() != "from" or not table_name:
        raise ValueError("Пример: select from users where age = 28")
    if not tail:
        return table_name, None

    (keyword,), conditions = _read_head(tail, 1)
    if keyword.lower() != "where":
        raise ValueError("После имени таблицы ожидается WHERE.")
    return table_name, _parse_assignments(_tokenize(conditions), "and")


def parse_update(user_input):
    """Возвращает имя таблицы, новые значения и условие WHERE."""
    (command, table_name, keyword), tail = _read_head(user_input, 3)
    if command.lower() != "update" or not table_name or keyword.lower() != "set":
        raise ValueError('Пример: update users set name = "Анна" where ID = 1')

    tokens = _tokenize(tail)
    where_index = next(
        (
            index
            for index in range(3, len(tokens), 4)
            if tokens[index].lower() == "where"
        ),
        None,
    )
    if where_index is None:
        raise ValueError("Для update нужно условие WHERE.")

    changes = _parse_assignments(tokens[:where_index], ",")
    conditions = _parse_assignments(tokens[where_index + 1:], "and")
    return table_name, changes, conditions


def parse_delete(user_input):
    """Возвращает имя таблицы и обязательное условие WHERE."""
    (command, source, table_name, keyword), tail = _read_head(user_input, 4)
    if (
        command.lower() != "delete"
        or source.lower() != "from"
        or not table_name
        or keyword.lower() != "where"
    ):
        raise ValueError("Пример: delete from users where ID = 1")
    return table_name, _parse_assignments(_tokenize(tail), "and")
