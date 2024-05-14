[![PyPI supported Python versions](https://img.shields.io/pypi/pyversions/better-automation.svg)](https://www.python.org/downloads/release/python-3116/)
## ⚙️ Настройки
После полной установки открываем файл `settings.py`, переходим к настройкам:
+ `DEBUG_MODE` - Настройка для отображения debug логов (0 или 1)
+ `SHUFFLE_ACCOUNTS` - перемешивать аккаунты (True) или идти по порядку (False)
+ `USE_PROXY` - использовать прокси (True) или нет (False)
+ `STRICT_PROXY` - строгость прокси (True) - будут работать только аккаунты для которых есть прокси в файле с проксями или нет (False) - прокси для аккаунтов будут выбраны по порядку
+ `SEMAPHORE_LIMIT` - количество аккаунтов, выполняющихся одновременно (аналог количества потоков), целое число
+ `NUMBER_OF_RETRIES` - количество попыток для проведения транзакции, целое число
+ `SLEEP_RANGE_BETWEEN_ACCOUNTS` - задержка между аккаунтами и попытками выполнить транзацию, два целых числа (минимум и максимум, каждый раз выбирается рандомно)
+ `TOKENS_SWAP_INPUT` - Монеты которые будут использоваться для обмена (Будет выбрана одна из списка) 
+ `TOKENS_SWAP_OUTPUT` - Монеты на которые будет произведен обмен (Будет выбрана одна из списка) 
+ `MIN_BALANCE` - Минимальный баланс на аккаунте для начала работы скрипта
+ `AMOUNT_PERCENT` - Процент от баланса для выполнения обмена (минимальное и максимальное значение от 1 до 100) будет использован в первом приоритете до `AMOUNT_QUANTITY`
+ `AMOUNT_QUANTITY` - Количество монет для обмена (минимальное и максимальное значение) для использования необходимо выставить`AMOUNT_PERCENT = ()`
+ `SLEEP_RANGE_BETWEEN_REVERSE_SWAP` - Задержка до запуска обратного обмена (минимум и максимум, каждый раз выбирается рандомно)
+ `REVERSE_SWAP` - Выполняет обратный обмен с тем же токеном (True) или (False)
+ `SWAPS_LIMIT_RANGE` - Количество обменов которые будут сделаны для каждого аккаунта, указывается диапозон от и до (1, 10). Значение будет выбранно рандомно из диапозона
+ `GAS_MULTIPLIER` - множитель газа для выполнения транзакции  (от 1 до 2 оптимальные значения с шагом 0.1)

## 🗂 Файлы
Основные файлы
+ `files/private_keys.txt` - ваши приватники
+ `files/proxy_list.txt` - ваши прокси, пример правильного формата в файле (если у вас прокси другого формата, можете попросить ChatGPT преобразовать их в нужный для софта)

Следующих файлов не будет при скачивании, но они будут созданы после первого запуска софта:
+ `files/log.txt` - все логи софта
+ `files/succeeded_wallets.txt` - аккаунты, на которых минт выполнен успешно (после каждого запуска очищается, поэтому тут будут данные с последнего запуска)
+ `files/failed_wallets.txt` - аккаунты, на которых минт не удался из-за какой-то ошибки (после каждого запуска очищается, поэтому тут будут данные с последнего запуска)

## Запуск софта
### Необходимо выполнить эти команды
- `pip install -r requirements.txt`
- `python main.py`