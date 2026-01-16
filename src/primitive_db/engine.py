from __future__ import annotations

import prompt


def welcome() -> None:
    print("***")
    print("<command> exit - выйти из программы")
    print("<command> help - справочная информация")


def run() -> None:
    while True:
        command = prompt.string(">>>Введите команду: ").strip()

        if command == "exit":
            break
        if command == "help":
            welcome()
            continue

        print(f'Функции {command} нет. Попробуйте снова.')