# SKY_DB_INF

---

## Курсовая работа № 3 

---

Консольное приложение на Python для получения данных о самолётах из API
nominatim.openstreetmap.org и opensky-network.org, фильтрации, сортировки и
сохранения результатов в JSON.

* [API nominatim openstreetmap](https://nominatim.openstreetmap.org/ui/search.html)
* [API opensky network](https://opensky-network.org/)

---

## 1. Описание проекта

Программа с терминальным меню, которая собирает данные о самолётах в воздушных
пространствах выбранных пользователем стран и сохраняет результат в JSON-файл.

### 1.1. Требования к окружению

Перед установкой проекта на ПК должны быть установлены не ниже:
```markdown
- Python 3.13
- Poetry
- Git
```
### 1.2. Проверка установленных версий

В терминале (CMD / PowerShell / Git Bash) используйте команды:


```markdown
python --version      # версия Python
```
```markdown
py -0                 # список установленных версий Python (Windows)
```
```markdown
poetry --version      # версия Poetry
```
```markdown
git --version         # версия Git
```
```markdown
git config --global user.name  # проверка, настроено ли имя пользователя в Git
```
Если какая-то команда не находится или версия Python меньше 3.13, нужно сначала установить/обновить соответствующий инструмент.

### 1.4. API key

Сервисы используют открытый API, ключи не требуются, что упрощает запуск приложения.

---

## 2. Установка и запуск

### 2.1. Установка

Клонируем проект к себе
```markdown
git clone https://github.com/Alex-399745146/sky_list.git
```
Входим в корневую папку проекта
```markdown
cd sky_list
```
В корневую папку устанавливаем все зависимости проекта
```markdown
poetry install
```
### 2.2. Запускаем
```markdown
poetry run python main.py
```

---

## 3. Использование

```markdown
После запуска программа запросит:
```
1. Название страны для запроса к API.
2. Количество самолётов для вывода в топ N.
3. Список стран регистрации (через пробел) для фильтрации.
4. Диапазон высот (например, 1000-15000).

Результат выводится таблицей в консоль и сохраняется без дубляжа в `data/aeroplanes.json`.

---

## 4. Структура проекта

- `src/api_clients.py` — работа с внешними API (Nominatim, OpenSky).
- `src/airplanes.py` — классы `BaseAeroplane` и `Aeroplane`, фильтрация и сравнение.
- `src/processing.py` — классы работы с JSON-файлом.
- `main.py` — точка входа, логика взаимодействия с пользователем.
- `tests/` — тесты на pytest.

---

## 5. Лицензия

Учебная работа по итогу окончания учебного модуля по ООП

### 5.1. Автор

Александр Бачевский (Alex Bachevskiy)

Telegram: [@bachevskiyaa](@bachevskiyaa)

Email: [bachevskiyaa@bk.ru](bachevskiyaa@bk.ru)

Email (Gmail): [bachevskiiaa@gmail.com](bachevskiiaa@gmail.com)

### 5.2. Лицензия
Учебный проект.

---