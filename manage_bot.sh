#!/bin/bash

case "$1" in
    start)
        echo "Запуск бота..."
        python bot.py >> bot.log 2>&1 &
        echo $! > bot.pid
        echo "Бот запущен. PID: $(cat bot.pid)"
        ;;
    stop)
        echo "Остановка бота..."
        if [ -f bot.pid ]; then
            kill $(cat bot.pid)
            rm bot.pid
            echo "Бот остановлен."
        else
            echo "Файл PID не найден."
        fi
        ;;
    restart)
        echo "Перезагрузка бота..."
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        if [ -f bot.pid ]; then
            if kill -0 $(cat bot.pid) 2>/dev/null; then
                echo "Бот работает. PID: $(cat bot.pid)"
            else
                echo "Бот не работает (файл PID существует)."
            fi
        else
            echo "Бот не работает."
        fi
        ;;
    logs)
        tail -f bot.log
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac