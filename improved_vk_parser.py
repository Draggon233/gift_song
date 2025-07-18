#!/usr/bin/env python3
"""
🎂 Улучшенный VK Birthday Parser для бота "Подари песню"

Система автоматического поиска людей с приближающимися днями рождения
в ВКонтакте и предложения их партнерам услуги поздравления через бота.
"""

import vk_api
import requests
import json
import time
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
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

class ImprovedVKParser:
    def __init__(self):
        """Инициализация улучшенного парсера ВКонтакте"""
        if not VK_TOKEN:
            raise ValueError("VK_TOKEN не настроен в config.py")
            
        self.vk_session = vk_api.VkApi(token=VK_TOKEN)
        self.vk = self.vk_session.get_api()
        
        # Для доступа к профилям пользователей
        if VK_USER_TOKEN:
            self.user_session = vk_api.VkApi(token=VK_USER_TOKEN)
            self.user_vk = self.user_session.get_api()
            logger.info("✅ Пользовательский токен настроен")
        else:
            self.user_vk = None
            logger.warning("⚠️ Пользовательский токен не настроен - ограниченная функциональность")
            
        self.birthday_data = self.load_birthday_data()
        
        # Популярные группы для поиска
        self.popular_groups = [
            '27895931',  # Подслушано
            '29534144',  # MDK
            '40316705',  # Лентач
            '147415230', # Борщ
            '154274761', # Смешные картинки
            '205865157', # Пикабу
            '1',         # ВКонтакте
            '2',         # ВКонтакте
            '3',         # ВКонтакте
            '4',         # ВКонтакте
            '5'          # ВКонтакте
        ]
        
    def load_birthday_data(self) -> Dict:
        """Загрузка данных о днях рождения из файла"""
        try:
            with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'processed_users': [], 'sent_messages': [], 'stats': {}}
            
    def save_birthday_data(self):
        """Сохранение данных о днях рождения в файл"""
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.birthday_data, f, ensure_ascii=False, indent=2)
            
    def get_birthday_range(self) -> Tuple[str, str]:
        """Получение диапазона дат для поиска дней рождения"""
        today = datetime.now()
        start_date = today + timedelta(days=BIRTHDAY_DAYS_RANGE[0])
        end_date = today + timedelta(days=BIRTHDAY_DAYS_RANGE[1])
        
        return start_date.strftime("%d.%m"), end_date.strftime("%d.%m")
        
    def search_birthday_users_advanced(self) -> List[Dict]:
        """Расширенный поиск пользователей с приближающимися днями рождения"""
        logger.info("🎯 Начинаю расширенный поиск пользователей с днями рождения...")
        
        birthday_users = []
        start_date, end_date = self.get_birthday_range()
        
        # Метод 1: Поиск по группам
        logger.info("📋 Метод 1: Поиск по популярным группам")
        group_users = self.search_in_groups()
        birthday_users.extend(group_users)
        
        # Метод 2: Поиск через поиск ВКонтакте
        logger.info("🔍 Метод 2: Поиск через поиск ВКонтакте")
        search_users = self.search_via_vk_search()
        birthday_users.extend(search_users)
        
        # Удаляем дубликаты
        unique_users = self.remove_duplicates(birthday_users)
        
        logger.info(f"✅ Найдено {len(unique_users)} уникальных пользователей с ДР через 7 дней")
        return unique_users
        
    def search_in_groups(self) -> List[Dict]:
        """Поиск пользователей в популярных группах"""
        users = []
        
        for group_id in self.popular_groups:
            try:
                logger.info(f"🔍 Поиск в группе {group_id}...")
                
                # Получаем участников группы
                members = self.vk.groups.getMembers(
                    group_id=group_id,
                    count=1000,
                    fields='bdate,sex,relation,relation_partner,first_name,last_name'
                )
                
                for member in members['items']:
                    if self._is_birthday_soon(member):
                        users.append(member)
                        
                time.sleep(PARSING_DELAY)
                
            except Exception as e:
                logger.error(f"❌ Ошибка при поиске в группе {group_id}: {e}")
                continue
                
        return users
        
    def search_via_vk_search(self) -> List[Dict]:
        """Поиск через поиск ВКонтакте"""
        users = []
        today = datetime.now()
        
        # Поиск по дням рождения в ближайшие 7 дней
        for days_ahead in range(BIRTHDAY_DAYS_RANGE[0], BIRTHDAY_DAYS_RANGE[1] + 1):
            search_date = today + timedelta(days=days_ahead)
            date_str = search_date.strftime("%d.%m")
            
            try:
                logger.info(f"🔍 Поиск пользователей с ДР {date_str}...")
                
                # Используем поиск пользователей
                search_results = self.vk.users.search(
                    q=f"день рождения {date_str}",
                    count=100,
                    fields='bdate,sex,relation,relation_partner,first_name,last_name'
                )
                
                for user in search_results['items']:
                    if self._is_birthday_soon(user):
                        users.append(user)
                        
                time.sleep(PARSING_DELAY)
                
            except Exception as e:
                logger.error(f"❌ Ошибка при поиске с ДР {date_str}: {e}")
                continue
                
        return users
        
    def _is_birthday_soon(self, user: Dict) -> bool:
        """Проверка, скоро ли день рождения у пользователя (ровно через 7 дней)"""
        if 'bdate' not in user or not user['bdate']:
            return False
            
        try:
            # Парсим дату рождения (формат: DD.MM.YYYY или DD.MM)
            bdate_parts = user['bdate'].split('.')
            if len(bdate_parts) < 2:
                return False
                
            bday_day = int(bdate_parts[0])
            bday_month = int(bdate_parts[1])
            
            # Проверяем, будет ли ДР ровно через 7 дней
            today = datetime.now()
            birthday_date = today + timedelta(days=7)
            
            return birthday_date.day == bday_day and birthday_date.month == bday_month
            
        except (ValueError, IndexError):
            return False
            
    def remove_duplicates(self, users: List[Dict]) -> List[Dict]:
        """Удаление дубликатов пользователей"""
        seen_ids = set()
        unique_users = []
        
        for user in users:
            if user['id'] not in seen_ids:
                seen_ids.add(user['id'])
                unique_users.append(user)
                
        return unique_users
        
    def get_user_partner(self, user_id: int) -> Optional[Dict]:
        """Получение информации о партнере пользователя"""
        if not self.user_vk:
            logger.warning("⚠️ Пользовательский токен не настроен, невозможно получить информацию о партнере")
            return None
            
        try:
            user_info = self.user_vk.users.get(
                user_ids=user_id,
                fields='relation,relation_partner,sex,first_name,last_name'
            )
            
            if not user_info:
                return None
                
            user = user_info[0]
            
            # Проверяем, есть ли партнер
            if 'relation_partner' in user and user['relation_partner']:
                partner_id = user['relation_partner']['id']
                
                # Получаем информацию о партнере
                partner_info = self.user_vk.users.get(
                    user_ids=partner_id,
                    fields='first_name,last_name,sex,domain,can_write_private_message'
                )
                
                if partner_info:
                    partner = partner_info[0]
                    
                    # Проверяем, можно ли отправить сообщение
                    if partner.get('can_write_private_message', 0) == 1:
                        return {
                            'id': partner['id'],
                            'name': f"{partner['first_name']} {partner['last_name']}",
                            'sex': partner.get('sex', 0),
                            'domain': partner.get('domain', ''),
                            'relation_type': user.get('relation', 0)
                        }
                    else:
                        logger.info(f"⚠️ Нельзя отправить сообщение партнеру {partner['id']}")
                        
        except Exception as e:
            logger.error(f"❌ Ошибка при получении информации о партнере пользователя {user_id}: {e}")
            
        return None
        
    def send_message_to_partner(self, partner: Dict, birthday_user: Dict) -> bool:
        """Отправка сообщения партнеру"""
        try:
            # Определяем пол именинника для выбора шаблона
            birthday_user_sex = birthday_user.get('sex', 0)
            
            # Выбираем шаблон сообщения
            if birthday_user_sex == 1:  # Женщина
                message_template = MESSAGE_TEMPLATES['male_partner'].format(BOT_LINK=BOT_LINK)
            else:  # Мужчина
                message_template = MESSAGE_TEMPLATES['female_partner'].format(BOT_LINK=BOT_LINK)
                
            # Отправляем сообщение через VK API
            if self.user_vk:
                try:
                    self.user_vk.messages.send(
                        user_id=partner['id'],
                        message=message_template,
                        random_id=int(time.time())
                    )
                    
                    # Сохраняем информацию об отправленном сообщении
                    self.birthday_data['sent_messages'].append({
                        'partner_id': partner['id'],
                        'partner_name': partner['name'],
                        'birthday_user_id': birthday_user['id'],
                        'birthday_user_name': f"{birthday_user.get('first_name', '')} {birthday_user.get('last_name', '')}",
                        'sent_at': datetime.now().isoformat(),
                        'message': message_template
                    })
                    
                    logger.info(f"✅ Сообщение отправлено партнеру {partner['name']} (ID: {partner['id']})")
                    return True
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка при отправке сообщения партнеру {partner['id']}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка при подготовке сообщения: {e}")
            
        return False
        
    def process_birthday_users(self):
        """Основной процесс обработки пользователей с днями рождения"""
        logger.info("🚀 Запуск процесса обработки пользователей с днями рождения...")
        
        # Получаем пользователей с приближающимися днями рождения
        birthday_users = self.search_birthday_users_advanced()
        
        processed_count = 0
        messages_sent = 0
        
        for user in birthday_users:
            user_id = user['id']
            user_name = f"{user.get('first_name', '')} {user.get('last_name', '')}"
            
            # Проверяем, не обрабатывали ли мы уже этого пользователя
            if user_id in self.birthday_data['processed_users']:
                logger.info(f"⏭️ Пользователь {user_name} уже обработан, пропускаем")
                continue
                
            try:
                logger.info(f"🔍 Обрабатываю пользователя: {user_name} (ID: {user_id})")
                
                # Получаем информацию о партнере
                partner = self.get_user_partner(user_id)
                
                if partner:
                    logger.info(f"💕 Найден партнер: {partner['name']}")
                    
                    # Отправляем сообщение партнеру
                    if self.send_message_to_partner(partner, user):
                        messages_sent += 1
                else:
                    logger.info(f"😔 Партнер не найден для пользователя {user_name}")
                        
                # Отмечаем пользователя как обработанного
                self.birthday_data['processed_users'].append(user_id)
                processed_count += 1
                
                # Задержка между запросами
                time.sleep(PARSING_DELAY)
                
            except Exception as e:
                logger.error(f"❌ Ошибка при обработке пользователя {user_id}: {e}")
                continue
                
        # Сохраняем данные
        self.save_birthday_data()
        
        # Обновляем статистику
        self.update_stats(processed_count, messages_sent)
        
        logger.info(f"✅ Обработка завершена:")
        logger.info(f"   📊 Обработано пользователей: {processed_count}")
        logger.info(f"   📨 Отправлено сообщений: {messages_sent}")
        
        return processed_count, messages_sent
        
    def update_stats(self, processed_count: int, messages_sent: int):
        """Обновление статистики"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        if 'stats' not in self.birthday_data:
            self.birthday_data['stats'] = {}
            
        if today not in self.birthday_data['stats']:
            self.birthday_data['stats'][today] = {
                'processed_users': 0,
                'messages_sent': 0,
                'runs': 0
            }
            
        self.birthday_data['stats'][today]['processed_users'] += processed_count
        self.birthday_data['stats'][today]['messages_sent'] += messages_sent
        self.birthday_data['stats'][today]['runs'] += 1

def main():
    """Основная функция"""
    try:
        parser = ImprovedVKParser()
        processed_count, messages_sent = parser.process_birthday_users()
        
        print(f"\n🎉 Результаты выполнения:")
        print(f"   👥 Обработано пользователей: {processed_count}")
        print(f"   📨 Отправлено сообщений: {messages_sent}")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()