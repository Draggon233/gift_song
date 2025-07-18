#!/usr/bin/env python3
"""
⏰ Улучшенный планировщик для VK Birthday Parser

Автоматический запуск поиска пользователей с днями рождения
и отправка предложений партнерам через бота "Подари песню".
"""

import schedule
import time
import logging
import json
from datetime import datetime, timedelta
from improved_vk_parser import ImprovedVKParser
from config import *

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ImprovedBirthdayScheduler:
    def __init__(self):
        """Инициализация улучшенного планировщика"""
        self.parser = None
        self.stats = self.load_stats()
        
    def load_stats(self) -> dict:
        """Загрузка статистики"""
        try:
            with open('scheduler_stats.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'total_runs': 0,
                'total_processed': 0,
                'total_messages': 0,
                'last_run': None,
                'daily_stats': {}
            }
            
    def save_stats(self):
        """Сохранение статистики"""
        with open('scheduler_stats.json', 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
            
    def run_birthday_check(self):
        """Запуск проверки дней рождения"""
        logger.info("🎯 Запуск запланированной проверки дней рождения...")
        
        try:
            # Инициализируем парсер
            if not self.parser:
                self.parser = ImprovedVKParser()
                
            # Запускаем обработку
            processed_count, messages_sent = self.parser.process_birthday_users()
            
            # Обновляем статистику
            self.update_stats(processed_count, messages_sent)
            
            logger.info(f"✅ Проверка завершена:")
            logger.info(f"   📊 Обработано: {processed_count}")
            logger.info(f"   📨 Отправлено сообщений: {messages_sent}")
            
            # Отправляем отчет в Telegram (если настроен)
            if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
                self.send_telegram_report(processed_count, messages_sent)
                
        except Exception as e:
            logger.error(f"❌ Ошибка при выполнении проверки дней рождения: {e}")
            
    def update_stats(self, processed_count: int, messages_sent: int):
        """Обновление статистики"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        self.stats['total_runs'] += 1
        self.stats['total_processed'] += processed_count
        self.stats['total_messages'] += messages_sent
        self.stats['last_run'] = datetime.now().isoformat()
        
        if today not in self.stats['daily_stats']:
            self.stats['daily_stats'][today] = {
                'runs': 0,
                'processed': 0,
                'messages': 0
            }
            
        self.stats['daily_stats'][today]['runs'] += 1
        self.stats['daily_stats'][today]['processed'] += processed_count
        self.stats['daily_stats'][today]['messages'] += messages_sent
        
        self.save_stats()
        
    def send_telegram_report(self, processed_count: int, messages_sent: int):
        """Отправка отчета в Telegram"""
        try:
            import telegram
            
            bot = telegram.Bot(token=TELEGRAM_TOKEN)
            
            # Формируем отчет
            report_message = f"""🎂 Отчет о проверке дней рождения

📊 Результаты:
✅ Обработано пользователей: {processed_count}
📨 Отправлено сообщений: {messages_sent}
⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}

📈 Общая статистика:
🔄 Всего запусков: {self.stats['total_runs']}
👥 Всего обработано: {self.stats['total_processed']}
📤 Всего сообщений: {self.stats['total_messages']}

{'🎉 Отличная работа! Сообщения отправлены!' if messages_sent > 0 else '😔 Сообщений не отправлено, но система работает'}"""
            
            bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=report_message
            )
            
            logger.info("✅ Отчет отправлен в Telegram")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке отчета в Telegram: {e}")
            
    def setup_schedule(self):
        """Настройка расписания"""
        # Основные запуски
        schedule.every().day.at("09:00").do(self.run_birthday_check)
        schedule.every().day.at("18:00").do(self.run_birthday_check)
        
        # Дополнительные запуски для лучшего покрытия
        schedule.every().day.at("12:00").do(self.run_birthday_check)
        schedule.every().day.at("21:00").do(self.run_birthday_check)
        
        logger.info("📅 Расписание настроено:")
        logger.info("   - 09:00 - Утренняя проверка")
        logger.info("   - 12:00 - Дневная проверка")
        logger.info("   - 18:00 - Вечерняя проверка")
        logger.info("   - 21:00 - Ночная проверка")
        
    def show_stats(self):
        """Показать статистику"""
        print(f"\n📊 Статистика планировщика:")
        print(f"   🔄 Всего запусков: {self.stats['total_runs']}")
        print(f"   👥 Всего обработано пользователей: {self.stats['total_processed']}")
        print(f"   📨 Всего отправлено сообщений: {self.stats['total_messages']}")
        
        if self.stats['last_run']:
            last_run = datetime.fromisoformat(self.stats['last_run'])
            print(f"   ⏰ Последний запуск: {last_run.strftime('%d.%m.%Y %H:%M')}")
            
        # Статистика за последние 7 дней
        print(f"\n📈 Статистика за последние 7 дней:")
        today = datetime.now()
        for i in range(7):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            if date_str in self.stats['daily_stats']:
                day_stats = self.stats['daily_stats'][date_str]
                print(f"   {date.strftime('%d.%m')}: {day_stats['processed']} обработано, {day_stats['messages']} сообщений")
            else:
                print(f"   {date.strftime('%d.%m')}: нет данных")
                
    def run(self):
        """Запуск планировщика"""
        logger.info("🚀 Запуск улучшенного планировщика дней рождения...")
        
        # Показываем статистику
        self.show_stats()
        
        # Настраиваем расписание
        self.setup_schedule()
        
        # Запускаем первую проверку сразу
        logger.info("🎯 Запуск первой проверки...")
        self.run_birthday_check()
        
        logger.info("⏰ Планировщик запущен. Ожидание следующего запуска...")
        
        # Запускаем бесконечный цикл
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Проверяем каждую минуту
                
            except KeyboardInterrupt:
                logger.info("⏹️ Планировщик остановлен пользователем")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в планировщике: {e}")
                time.sleep(300)  # Ждем 5 минут при ошибке

def main():
    """Основная функция"""
    try:
        scheduler = ImprovedBirthdayScheduler()
        scheduler.run()
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()