## Шаги по настройки


### Шаг 1: Создайте виртуальное окружение
Создайте виртуальное окружение в папке `.venv`:

```sh
python3 -m venv .venv
```

### Шаг 2: Активируйте виртуальное окружение
Активация виртуального окружения зависит от вашей операционной системы.

#### Для Windows:
```sh
.venv\Scripts\activate
```

#### Для macOS и Linux:
```sh
source .venv/bin/activate
```

После активации виртуального окружения вы увидите, что в начале строки терминала появилось имя окружения (например, `(.venv)`).

### Шаг 3: Установите необходимые пакеты
Теперь, когда виртуальное окружение активировано, вы можете устанавливать необходимые пакеты с помощью `pip`. Например:

```sh
pip3 install -r requirements.txt
```