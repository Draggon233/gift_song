#!/usr/bin/env python3
"""
🎂 Запуск системы парсинга дней рождения для бота "Подари песню"

Простой интерфейс для запуска парсера и планировщика.
"""

import sys
import os
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_banner():
    """Вывод баннера"""
    print("🎂" * 50)
    print("🎂 VK Birthday Parser для бота 'Подари песню'")
    print("🎂" * 50)
    print()

def check_config():
    """Проверка конфигурации"""
    print("🔧 Проверка конфигурации...")
    
    try:
        from config import VK_TOKEN, VK_USER_TOKEN, BOT_LINK
        
        if not VK_TOKEN:
            print("❌ VK_TOKEN не настроен")
            print("   Получите токен на https://vkhost.github.io/")
            return False
        else:
            print("✅ VK_TOKEN настроен")
            
        if not VK_USER_TOKEN:
            print("⚠️  VK_USER_TOKEN не настроен (ограниченная функциональность)")
            print("   Получите токен пользователя на https://vkhost.github.io/")
        else:
            print("✅ VK_USER_TOKEN настроен")
            
        print(f"✅ Ссылка на бота: {BOT_LINK}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта конфигурации: {e}")
        return False

def run_single_parse():
    """Запуск однократного парсинга"""
    print("🔍 Запуск однократного парсинга...")
    
    try:
        from improved_vk_parser import ImprovedVKParser
        
        parser = ImprovedVKParser()
        processed_count, messages_sent = parser.process_birthday_users()
        
        print(f"\n🎉 Результаты парсинга:")
        print(f"   👥 Обработано пользователей: {processed_count}")
        print(f"   📨 Отправлено сообщений: {messages_sent}")
        
    except Exception as e:
        print(f"❌ Ошибка при парсинге: {e}")

def run_scheduler():
    """Запуск планировщика"""
    print("⏰ Запуск планировщика...")
    print("   Планировщик будет запускать парсинг автоматически")
    print("   Расписание: 09:00, 12:00, 18:00, 21:00")
    print("   Для остановки нажмите Ctrl+C")
    print()
    
    try:
        from improved_scheduler import ImprovedBirthdayScheduler
        
        scheduler = ImprovedBirthdayScheduler()
        scheduler.run()
        
    except KeyboardInterrupt:
        print("\n⏹️ Планировщик остановлен")
    except Exception as e:
        print(f"❌ Ошибка планировщика: {e}")

def show_help():
    """Показать справку"""
    print("📖 Справка по использованию:")
    print()
    print("1. Настройка токенов:")
    print("   - Скопируйте env_example.txt в .env")
    print("   - Получите VK токены на https://vkhost.github.io/")
    print("   - Заполните токены в файле .env")
    print()
    print("2. Установка зависимостей:")
    print("   pip install -r requirements.txt")
    print()
    print("3. Запуск:")
    print("   python start_birthday_parser.py")
    print()
    print("4. Режимы работы:")
    print("   1 - Однократный парсинг")
    print("   2 - Запуск планировщика")
    print("   3 - Справка")
    print("   4 - Выход")

def main():
    """Главная функция"""
    print_banner()
    
    # Проверяем конфигурацию
    if not check_config():
        print("\n❌ Пожалуйста, настройте конфигурацию перед запуском")
        print("   Смотрите файл env_example.txt для инструкций")
        return
    
    print("\n🎯 Выберите режим работы:")
    print("1. 🔍 Однократный парсинг")
    print("2. ⏰ Запуск планировщика")
    print("3. 📖 Справка")
    print("4. ❌ Выход")
    
    while True:
        try:
            choice = input("\nВведите номер (1-4): ").strip()
            
            if choice == '1':
                run_single_parse()
                break
            elif choice == '2':
                run_scheduler()
                break
            elif choice == '3':
                show_help()
                print("\n🎯 Выберите режим работы:")
                print("1. 🔍 Однократный парсинг")
                print("2. ⏰ Запуск планировщика")
                print("3. 📖 Справка")
                print("4. ❌ Выход")
            elif choice == '4':
                print("👋 До свидания!")
                break
            else:
                print("❌ Неверный выбор. Введите число от 1 до 4.")
                
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()