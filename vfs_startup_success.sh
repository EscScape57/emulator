#!/bin/bash

echo "Запуск VFS стартового скрипта"

# Тестирование ls
ls
ls home
ls home/user

# Тестирование cd
cd home
ls
cd user
ls
cd ../..
ls

echo "VFS стартовый скрипт завершен."
