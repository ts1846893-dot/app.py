import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
import aiohttp
import hashlib
import hmac
from urllib.parse import urlencode
import json
import random
from typing import Dict, List, Optional

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Конфигурация
BOT_TOKEN = "8281958666:AAHNA1903HsTFIKk9EIzo8iZTDRubd9Efio"
CRYPTO_PAY_TOKEN = "460274:AA4zckIq0DlJPxe6J54euvqE0Cyc95CcvUO"
CASINO_CHANNEL_ID = -1003045077123
CASINO_CHANNEL_URL = "https://t.me/cryptorush_24_7"
NEWS_CHANNEL_URL = "https://t.me/worldauk"
SUPPORT_USERNAME = "@Dimfulsvazbot"
BETS_CHANNEL_ID = -1003045077123
ADMIN_USERNAMES = ["Dimful_dmf", "S21_M_A"]
WEB_APP_URL = "https://python-template-a5c8.replit.app"

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния FSM
class UserStates(StatesGroup):
    waiting_deposit_amount = State()
    waiting_bet_amount = State()
    selecting_balance = State()
    waiting_username = State()
    waiting_bonus_amount = State()
    waiting_promo_code = State()
    waiting_withdrawal_amount = State()

    # Игровые состояния
    playing_dice_dynasty = State()
    playing_crash_rocket = State()
    playing_slot_legends = State()
    playing_roulette_rush = State()
    playing_blackjack_battle = State()
    playing_mines_mayhem = State()
    playing_wheel_wizard = State()
    playing_coin_clash = State()
    playing_poker_pro = State()
    playing_baccarat_blitz = State()

    # Состояния кейсов
    opening_case = State()
    selecting_case = State()

# Константы для игр и кейсов
GAMES_CONFIG = {
    'coin_clash': {'name': 'Coin Clash', 'emoji': '🪙', 'max_multiplier': 2.0, 'min_bet': 0.5},
    'dice_dynasty': {'name': 'Dice Dynasty', 'emoji': '🎲', 'max_multiplier': 6.0, 'min_bet': 0.5},
    'crash_rocket': {'name': 'Crash Rocket', 'emoji': '🚀', 'max_multiplier': 100.0, 'min_bet': 1.0},
    'slot_legends': {'name': 'Slot Legends', 'emoji': '🎰', 'max_multiplier': 1000.0, 'min_bet': 0.5},
    'roulette_rush': {'name': 'Roulette Rush', 'emoji': '🎯', 'max_multiplier': 36.0, 'min_bet': 1.0},
    'blackjack_battle': {'name': 'Blackjack Battle', 'emoji': '🃏', 'max_multiplier': 2.5, 'min_bet': 1.0},
    'mines_mayhem': {'name': 'Mines Mayhem', 'emoji': '💎', 'max_multiplier': 50.0, 'min_bet': 0.5},
    'wheel_wizard': {'name': 'Wheel Wizard', 'emoji': '🎨', 'max_multiplier': 20.0, 'min_bet': 0.5},
    'poker_pro': {'name': 'Poker Pro', 'emoji': '♠️', 'max_multiplier': 10.0, 'min_bet': 2.0},
    'baccarat_blitz': {'name': 'Baccarat Blitz', 'emoji': '💳', 'max_multiplier': 2.0, 'min_bet': 1.0}
}

CASES_CONFIG = {
    'cs_go_classic': {'name': 'CS:GO Classic', 'price': 5.0, 'emoji': '📦'},
    'knife_collection': {'name': 'Knife Collection', 'price': 25.0, 'emoji': '🔪'},
    'rare_skins': {'name': 'Rare Skins', 'price': 10.0, 'emoji': '✨'},
    'glove_case': {'name': 'Glove Case', 'price': 15.0, 'emoji': '🧤'},
    'weapon_master': {'name': 'Weapon Master', 'price': 20.0, 'emoji': '🔫'},
    'legend_box': {'name': 'Legend Box', 'price': 50.0, 'emoji': '👑'},
    'starter_pack': {'name': 'Starter Pack', 'price': 2.0, 'emoji': '🎁'},
    'premium_vault': {'name': 'Premium Vault', 'price': 100.0, 'emoji': '💎'},
    'mystery_chest': {'name': 'Mystery Chest', 'price': 7.5, 'emoji': '❓'},
    'golden_cache': {'name': 'Golden Cache', 'price': 75.0, 'emoji': '🏆'}
}

ITEMS_POOL = [
    # Обычные предметы (Common)
    {'name': 'AK-47 | Redline', 'rarity': 'common', 'value': 5.0, 'chance': 30},
    {'name': 'M4A4 | Howl', 'rarity': 'common', 'value': 8.0, 'chance': 25},
    {'name': 'AWP | Dragon Lore', 'rarity': 'common', 'value': 12.0, 'chance': 20},

    # Редкие предметы (Rare)
    {'name': 'Butterfly Knife | Fade', 'rarity': 'rare', 'value': 50.0, 'chance': 15},
    {'name': 'Karambit | Doppler', 'rarity': 'rare', 'value': 75.0, 'chance': 8},

    # Легендарные предметы (Legendary)
    {'name': 'Dragon Lore Souvenir', 'rarity': 'legendary', 'value': 200.0, 'chance': 1.5},
    {'name': 'Karambit | Case Hardened', 'rarity': 'legendary', 'value': 500.0, 'chance': 0.5}
]

PROMO_CODES = {
    'WELCOME2024': {'bonus': 10.0, 'uses_left': 100, 'type': 'bonus'},
    'RUSH100': {'bonus': 25.0, 'uses_left': 50, 'type': 'main'},
    'CRYPTO50': {'bonus': 5.0, 'uses_left': 200, 'type': 'bonus'},
    'VIP2024': {'bonus': 100.0, 'uses_left': 10, 'type': 'main'}
}

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()

    # Таблица пользователей (расширенная)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        balance REAL DEFAULT 0,
        bonus_balance REAL DEFAULT 0,
        rush_coins INTEGER DEFAULT 0,
        bonus_points INTEGER DEFAULT 0,
        loyalty_tokens INTEGER DEFAULT 0,
        total_bets REAL DEFAULT 0,
        games_played INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        referral_earnings REAL DEFAULT 0,
        referrals_count INTEGER DEFAULT 0,
        referrer_id INTEGER,
        registration_date TEXT,
        ref_link TEXT,
        level INTEGER DEFAULT 1,
        experience INTEGER DEFAULT 0,
        daily_streak INTEGER DEFAULT 0,
        last_daily_claim TEXT,
        premium_expires TEXT,
        achievements TEXT DEFAULT '[]',
        inventory TEXT DEFAULT '[]',
        current_mission TEXT DEFAULT '{}',
        dice_boosts INTEGER DEFAULT 0,
        crash_insurance INTEGER DEFAULT 0,
        slot_multiplier REAL DEFAULT 1.0
    )''')

    # Таблица транзакций
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        currency TEXT DEFAULT 'USDT',
        type TEXT,
        date TEXT,
        check_id TEXT,
        status TEXT DEFAULT 'completed'
    )''')

    # Таблица игр (расширенная)
    c.execute('''CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        game_type TEXT,
        bet_amount REAL,
        win_amount REAL,
        result TEXT,
        multiplier REAL,
        date TEXT,
        details TEXT DEFAULT '{}'
    )''')

    # Таблица турниров
    c.execute('''CREATE TABLE IF NOT EXISTS tournaments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        game_type TEXT,
        start_date TEXT,
        end_date TEXT,
        prize_pool REAL,
        participants TEXT DEFAULT '[]',
        status TEXT DEFAULT 'upcoming'
    )''')

    # Таблица лидерборда турниров
    c.execute('''CREATE TABLE IF NOT EXISTS tournament_leaderboard (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tournament_id INTEGER,
        user_id INTEGER,
        score REAL DEFAULT 0,
        games_played INTEGER DEFAULT 0,
        last_update TEXT
    )''')

    # Таблица достижений
    c.execute('''CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        reward_type TEXT,
        reward_amount REAL,
        condition_type TEXT,
        condition_value INTEGER
    )''')

    # Таблица миссий
    c.execute('''CREATE TABLE IF NOT EXISTS missions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        reward_type TEXT,
        reward_amount REAL,
        condition_type TEXT,
        condition_value INTEGER,
        daily BOOLEAN DEFAULT 0
    )''')

    # Таблица использованных промокодов
    c.execute('''CREATE TABLE IF NOT EXISTS used_promocodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        promo_code TEXT,
        used_date TEXT
    )''')

    # Заполнение достижений
    achievements = [
        ("Первая ставка", "Сделайте первую ставку", "rush_coins", 100, "games_played", 1),
        ("Везунчик", "Выиграйте 10 игр подряд", "bonus_points", 500, "win_streak", 10),
        ("Хайроллер", "Поставьте 1000 USDT за раз", "loyalty_tokens", 50, "single_bet", 1000),
        ("Марафонец", "Сыграйте 100 игр", "rush_coins", 1000, "games_played", 100),
        ("Миллионер", "Выиграйте 10000 USDT", "loyalty_tokens", 200, "total_wins", 10000)
    ]

    for achievement in achievements:
        c.execute("INSERT OR IGNORE INTO achievements (name, description, reward_type, reward_amount, condition_type, condition_value) VALUES (?, ?, ?, ?, ?, ?)", achievement)

    # Заполнение миссий
    missions = [
        ("Ежедневная удача", "Сыграйте 5 игр", "bonus_points", 50, "daily_games", 5, 1),
        ("Удачливый час", "Выиграйте 3 игры", "rush_coins", 100, "daily_wins", 3, 1),
        ("Инвестор", "Пополните баланс на 10 USDT", "loyalty_tokens", 10, "daily_deposit", 10, 1)
    ]

    for mission in missions:
        c.execute("INSERT OR IGNORE INTO missions (name, description, reward_type, reward_amount, condition_type, condition_value, daily) VALUES (?, ?, ?, ?, ?, ?, ?)", mission)

    conn.commit()
    conn.close()

# Функции работы с базой данных
def get_user(user_id):
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def create_user(user_id, username, first_name, referrer_id=None):
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()

    ref_link = f"https://t.me/CryptoRushCazino_Bot?start={user_id}"
    registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Стартовые бонусы
    starting_bonus = 5.0
    starting_rush_coins = 1000
    starting_bonus_points = 100

    c.execute("""INSERT INTO users (
        user_id, username, first_name, referrer_id, registration_date, ref_link,
        bonus_balance, rush_coins, bonus_points
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
              (user_id, username, first_name, referrer_id, registration_date, ref_link,
               starting_bonus, starting_rush_coins, starting_bonus_points))

    conn.commit()
    conn.close()

def update_user_balance(user_id, amount, balance_type='main'):
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()

    if balance_type == 'main':
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    elif balance_type == 'bonus':
        c.execute("UPDATE users SET bonus_balance = bonus_balance + ? WHERE user_id = ?", (amount, user_id))
    elif balance_type == 'rush_coins':
        c.execute("UPDATE users SET rush_coins = rush_coins + ? WHERE user_id = ?", (amount, user_id))
    elif balance_type == 'bonus_points':
        c.execute("UPDATE users SET bonus_points = bonus_points + ? WHERE user_id = ?", (amount, user_id))
    elif balance_type == 'loyalty_tokens':
        c.execute("UPDATE users SET loyalty_tokens = loyalty_tokens + ? WHERE user_id = ?", (amount, user_id))

    conn.commit()
    conn.close()

def get_user_level_info(user_id):
    user = get_user(user_id)
    if not user:
        return None

    experience = user[18]
    level = user[17]

    # Формула уровня: следующий уровень = текущий_уровень * 1000
    exp_for_next = level * 1000

    return {
        'level': level,
        'experience': experience,
        'exp_for_next': exp_for_next,
        'progress': (experience / exp_for_next) * 100 if exp_for_next > 0 else 0
    }

def add_experience(user_id, exp_amount):
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()

    user = get_user(user_id)
    if not user:
        conn.close()
        return

    current_exp = user[18]
    current_level = user[17]
    new_exp = current_exp + exp_amount

    # Проверка повышения уровня
    exp_needed = current_level * 1000
    new_level = current_level

    while new_exp >= exp_needed:
        new_exp -= exp_needed
        new_level += 1
        exp_needed = new_level * 1000

        # Награда за повышение уровня
        level_reward = new_level * 100  # RUSH Coins
        c.execute("UPDATE users SET rush_coins = rush_coins + ? WHERE user_id = ?", (level_reward, user_id))

    c.execute("UPDATE users SET experience = ?, level = ? WHERE user_id = ?", (new_exp, new_level, user_id))
    conn.commit()
    conn.close()

    return new_level > current_level  # Возвращает True если был повышен уровень

def check_daily_bonus(user_id):
    user = get_user(user_id)
    if not user:
        return False

    last_claim = user[20]  # last_daily_claim
    if not last_claim:
        return True

    last_claim_date = datetime.strptime(last_claim, "%Y-%m-%d")
    today = datetime.now().date()

    return today > last_claim_date

def claim_daily_bonus(user_id):
    if not check_daily_bonus(user_id):
        return None

    conn = sqlite3.connect('casino.db')
    c = conn.cursor()

    user = get_user(user_id)
    streak = user[19] + 1  # daily_streak

    # Бонус увеличивается со стриком
    base_bonus = 2.0
    bonus_amount = base_bonus + (streak * 0.5)
    rush_coins = 50 + (streak * 10)

    if streak >= 7:  # Недельный бонус
        bonus_amount *= 2
        rush_coins *= 2

    today = datetime.now().strftime("%Y-%m-%d")

    c.execute("""UPDATE users SET 
                 bonus_balance = bonus_balance + ?,
                 rush_coins = rush_coins + ?,
                 daily_streak = ?,
                 last_daily_claim = ?
                 WHERE user_id = ?""", 
              (bonus_amount, rush_coins, streak, today, user_id))

    conn.commit()
    conn.close()

    return {'bonus': bonus_amount, 'rush_coins': rush_coins, 'streak': streak}

# Проверка подписки на канал
async def check_subscription(user_id):
    try:
        member = await bot.get_chat_member(CASINO_CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking subscription for user {user_id}: {e}")
        return True  # Разрешаем доступ при ошибке

# Генерация клавиатур
def get_subscription_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Перейти к каналу", url=CASINO_CHANNEL_URL)],
        [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription")]
    ])
    return keyboard

def get_main_menu_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть", callback_data="games_menu"), 
         InlineKeyboardButton(text="📦 Кейсы", callback_data="cases_menu")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"), 
         InlineKeyboardButton(text="🏆 Турниры", callback_data="tournaments")],
        [InlineKeyboardButton(text="🎯 Миссии", callback_data="missions"), 
         InlineKeyboardButton(text="🤝 Рефералы", callback_data="referral")],
        [InlineKeyboardButton(text="🌐 Веб-казино", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="💬 Поддержка", callback_data="support")]
    ])
    return keyboard

def get_games_keyboard():
    builder = InlineKeyboardBuilder()

    for game_id, config in GAMES_CONFIG.items():
        builder.button(
            text=f"{config['emoji']} {config['name']}",
            callback_data=f"game_{game_id}"
        )

    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"))
    return builder.as_markup()

def get_cases_keyboard():
    builder = InlineKeyboardBuilder()

    for case_id, config in CASES_CONFIG.items():
        builder.button(
            text=f"{config['emoji']} {config['name']} - {config['price']} USDT",
            callback_data=f"case_{case_id}"
        )

    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inventory"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"))
    return builder.as_markup()

def get_profile_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance"),
         InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="🏆 Достижения", callback_data="achievements"),
         InlineKeyboardButton(text="🎁 Ежедневный бонус", callback_data="daily_bonus")],
        [InlineKeyboardButton(text="🎯 Промокод", callback_data="promo"),
         InlineKeyboardButton(text="👑 Премиум", callback_data="premium")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    return keyboard

def get_balance_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Пополнить", callback_data="deposit"),
         InlineKeyboardButton(text="💸 Вывести", callback_data="withdraw")],
        [InlineKeyboardButton(text="💱 Обменять валюты", callback_data="exchange")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="profile")]
    ])
    return keyboard

# Функции CryptoPay API (расширенные)
async def create_invoice(amount=1.0, asset='USDT'):
    url = "https://pay.crypt.bot/api/createInvoice"
    headers = {
        "Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN,
        "Content-Type": "application/json"
    }

    data = {
        "asset": asset,
        "amount": str(amount),
        "description": f"Пополнение баланса Crypto Rush Casino - {amount} {asset}"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('ok'):
                        return result.get('result')
                return None
    except Exception as e:
        logger.error(f"Exception in create_invoice: {e}")
        return None

async def check_invoice(invoice_id):
    url = f"https://pay.crypt.bot/api/getInvoices"
    headers = {
        "Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN,
        "Content-Type": "application/json"
    }

    params = {"invoice_ids": invoice_id}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('ok'):
                        invoices = result.get('result', {}).get('items', [])
                        if invoices:
                            invoice_data = invoices[0]
                            return {
                                'status': invoice_data.get('status'),
                                'amount': float(invoice_data.get('amount', 0)),
                                'asset': invoice_data.get('asset', 'USDT'),
                                'paid': invoice_data.get('status') == 'paid'
                            }
                return {'status': 'unknown', 'amount': 0, 'asset': 'USDT', 'paid': False}
    except Exception as e:
        logger.error(f"Exception in check_invoice: {e}")
        return {'status': 'unknown', 'amount': 0, 'asset': 'USDT', 'paid': False}

# Игровые функции
def play_coin_clash(bet_amount, selected_side):
    """PvP орёл/решка"""
    result = random.choice(['heads', 'tails'])
    win = result == selected_side

    if win:
        multiplier = 1.95  # Небольшая комиссия казино
        win_amount = bet_amount * multiplier
        return {'win': True, 'multiplier': multiplier, 'win_amount': win_amount, 'result': result}
    else:
        return {'win': False, 'multiplier': 0, 'win_amount': 0, 'result': result}

def play_dice_dynasty(bet_amount, user_boosts=0):
    """Прокачиваемые кости с бустами"""
    dice_results = [random.randint(1, 6) for _ in range(2)]
    total = sum(dice_results)

    # Применение бустов
    if user_boosts > 0:
        boost_chance = min(user_boosts * 0.05, 0.3)  # До 30% шанса буста
        if random.random() < boost_chance:
            total = min(total + random.randint(1, 3), 12)

    # Таблица выплат для суммы костей
    multipliers = {
        2: 35, 3: 17, 4: 11, 5: 8, 6: 6, 7: 5,
        8: 6, 9: 8, 10: 11, 11: 17, 12: 35
    }

    multiplier = multipliers.get(total, 1)
    win = total in [2, 3, 11, 12] or random.random() < 0.4

    if win:
        win_amount = bet_amount * multiplier
        return {'win': True, 'multiplier': multiplier, 'win_amount': win_amount, 'dice': dice_results, 'total': total}
    else:
        return {'win': False, 'multiplier': 0, 'win_amount': 0, 'dice': dice_results, 'total': total}

def play_crash_rocket(bet_amount, cash_out_at=None):
    """Космический корабль с множителями до x100"""
    # Симуляция краш-игры
    crash_point = random.uniform(1.01, 100.0)

    # Экспоненциальное распределение для реалистичности
    if random.random() < 0.7:  # 70% игр крашатся рано
        crash_point = random.uniform(1.01, 3.0)
    elif random.random() < 0.9:  # 20% игр крашатся в середине
        crash_point = random.uniform(3.0, 10.0)
    # 10% игр идут высоко

    if cash_out_at and cash_out_at < crash_point:
        # Игрок успел забрать
        win_amount = bet_amount * cash_out_at
        return {'win': True, 'multiplier': cash_out_at, 'win_amount': win_amount, 'crash_point': crash_point}
    else:
        # Игрок не успел или не указал точку выхода
        return {'win': False, 'multiplier': 0, 'win_amount': 0, 'crash_point': crash_point}

def play_slot_legends(bet_amount, user_multiplier=1.0):
    """Слоты с легендарными джекпотами"""
    symbols = ['🍒', '🍋', '🍊', '🍇', '⭐', '💎', '🎰', '🏆']
    weights = [25, 20, 15, 15, 10, 8, 4, 3]  # Веса для символов

    reels = []
    for _ in range(3):
        reel = random.choices(symbols, weights=weights, k=1)[0]
        reels.append(reel)

    # Проверка выигрышных комбинаций
    if reels[0] == reels[1] == reels[2]:  # Три одинаковых
        symbol_multipliers = {
            '🍒': 5, '🍋': 10, '🍊': 15, '🍇': 20,
            '⭐': 50, '💎': 100, '🎰': 500, '🏆': 1000
        }
        base_multiplier = symbol_multipliers.get(reels[0], 5)
        final_multiplier = base_multiplier * user_multiplier
        win_amount = bet_amount * final_multiplier
        return {'win': True, 'multiplier': final_multiplier, 'win_amount': win_amount, 'reels': reels}
    elif reels[0] == reels[1] or reels[1] == reels[2]:  # Два одинаковых
        base_multiplier = 2 * user_multiplier
        win_amount = bet_amount * base_multiplier
        return {'win': True, 'multiplier': base_multiplier, 'win_amount': win_amount, 'reels': reels}
    else:
        return {'win': False, 'multiplier': 0, 'win_amount': 0, 'reels': reels}

def open_case(case_type, user_id):
    """Открытие кейса"""
    case_config = CASES_CONFIG.get(case_type)
    if not case_config:
        return None

    # Выбор предмета на основе шансов
    total_chance = sum(item['chance'] for item in ITEMS_POOL)
    rand_value = random.uniform(0, total_chance)

    current_chance = 0
    for item in ITEMS_POOL:
        current_chance += item['chance']
        if rand_value <= current_chance:
            # Добавление предмета в инвентарь
            add_item_to_inventory(user_id, item)
            return item

    # Если что-то пошло не так, возвращаем первый предмет
    return ITEMS_POOL[0]

def add_item_to_inventory(user_id, item):
    """Добавление предмета в инвентарь"""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()

    user = get_user(user_id)
    if not user:
        conn.close()
        return

    try:
        # Проверяем, есть ли колонка inventory (индекс 24)
        if len(user) > 24 and user[24]:
            inventory = json.loads(user[24])
        else:
            inventory = []
    except:
        inventory = []

    # Добавляем предмет с временной меткой
    item_with_timestamp = {
        **item,
        'received_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'id': len(inventory) + 1
    }

    inventory.append(item_with_timestamp)

    c.execute("UPDATE users SET inventory = ? WHERE user_id = ?", (json.dumps(inventory), user_id))
    conn.commit()
    conn.close()

def get_user_inventory(user_id):
    """Получение инвентаря пользователя"""
    user = get_user(user_id)
    if not user:
        return []

    try:
        if len(user) > 24 and user[24]:
            return json.loads(user[24])
        else:
            return []
    except:
        return []

# Обработчики команд
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # Проверка реферальной ссылки
    referrer_id = None
    if len(message.text.split()) > 1:
        try:
            referrer_id = int(message.text.split()[1])
            if referrer_id == user_id:
                referrer_id = None
            elif get_user(referrer_id) is None:
                referrer_id = None
        except:
            pass

    # Проверка подписки
    if not await check_subscription(user_id):
        await message.answer(
            "🔒 Для использования бота обязательно быть подписанным на канал!",
            reply_markup=get_subscription_keyboard()
        )
        return

    # Проверка существования пользователя
    user = get_user(user_id)
    is_new_user = user is None

    if is_new_user:
        create_user(user_id, username, first_name, referrer_id)
        logger.info(f"New user registered: {user_id} (@{username})")

        # Начисление бонуса рефереру
        if referrer_id:
            conn = sqlite3.connect('casino.db')
            c = conn.cursor()
            c.execute("UPDATE users SET referrals_count = referrals_count + 1, bonus_balance = bonus_balance + 5 WHERE user_id = ?", (referrer_id,))
            conn.commit()
            conn.close()

        welcome_text = f"""🎉 Добро пожаловать в Crypto Rush Casino!

🎁 Стартовые бонусы:
💎 5.0 USDT бонусного баланса
🪙 1000 RUSH Coins
⭐ 100 Bonus Points

{'🤝 Вы пришли по реферальной ссылке - ваш реферер получил 5 USDT!' if referrer_id else ''}

🌟 Особенности нашего казино:
• 10 уникальных игр с особыми механиками
• Система кейсов с CS:GO предметами
• Трёхуровневая реферальная система
• Ежедневные миссии и турниры
• Веб-приложение для полного погружения

🎰 Канал: {CASINO_CHANNEL_URL}
📢 Новости: {NEWS_CHANNEL_URL}"""

        await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())
    else:
        await show_main_menu(message)

async def show_main_menu(message):
    user = get_user(message.from_user.id)
    username = message.from_user.username or user[2]  # first_name
    level_info = get_user_level_info(message.from_user.id)

    welcome_text = f"""👋 Добро пожаловать, {username}!

📊 Ваш уровень: {level_info['level']} (опыт: {level_info['experience']}/{level_info['exp_for_next']})
💰 Балансы:
  • Основной: {user[3]:.2f} USDT
  • Бонусный: {user[4]:.2f} USDT
  • RUSH Coins: {user[5]:,}
  • Bonus Points: {user[6]:,}
  • Loyalty Tokens: {user[7]:,}

🎰 Канал: {CASINO_CHANNEL_URL}
📢 Новости: {NEWS_CHANNEL_URL}"""

    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())

# Обработчики callback_query
@dp.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    if await check_subscription(user_id):
        await callback_query.message.delete()
        await show_main_menu(callback_query.message)
    else:
        await callback_query.answer("❌ Вы не подписались на канал!")

@dp.callback_query(F.data == "main_menu")
async def main_menu_callback(callback_query: types.CallbackQuery):
    user = get_user(callback_query.from_user.id)
    username = callback_query.from_user.username or user[2]
    level_info = get_user_level_info(callback_query.from_user.id)

    welcome_text = f"""👋 Добро пожаловать, {username}!

📊 Ваш уровень: {level_info['level']} (опыт: {level_info['experience']}/{level_info['exp_for_next']})
💰 Балансы:
  • Основной: {user[3]:.2f} USDT
  • Бонусный: {user[4]:.2f} USDT
  • RUSH Coins: {user[5]:,}
  • Bonus Points: {user[6]:,}
  • Loyalty Tokens: {user[7]:,}

🎰 Канал: {CASINO_CHANNEL_URL}
📢 Новости: {NEWS_CHANNEL_URL}"""

    await callback_query.message.edit_text(welcome_text, reply_markup=get_main_menu_keyboard())

@dp.callback_query(F.data == "games_menu")
async def games_menu_callback(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text(
        "🎮 Выберите игру:\n\n" +
        "🪙 Coin Clash - PvP орёл/решка с live-соперником\n" +
        "🎲 Dice Dynasty - Прокачиваемые кости с бустами\n" +
        "🚀 Crash Rocket - Космический корабль до x100\n" +
        "🎰 Slot Legends - Слоты с легендарными джекпотами\n" +
        "🎯 Roulette Rush - Молниеносная рулетка\n" +
        "🃏 Blackjack Battle - Турнирный блэкджек\n" +
        "💎 Mines Mayhem - Сапёр с криптовалютами\n" +
        "🎨 Wheel Wizard - Магическое колесо фортуны\n" +
        "♠️ Poker Pro - Профессиональный покер\n" +
        "💳 Baccarat Blitz - Молниеносный баккара",
        reply_markup=get_games_keyboard()
    )

@dp.callback_query(F.data == "cases_menu")
async def cases_menu_callback(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text(
        "📦 Кейсы с CS:GO предметами:\n\n" +
        "Откройте кейсы и получите редкие скины!\n" +
        "От обычных предметов до легендарных ножей.\n\n" +
        "💎 Редкость предметов:\n" +
        "• Common - обычные предметы\n" +
        "• Rare - редкие предметы\n" +
        "• Legendary - легендарные предметы",
        reply_markup=get_cases_keyboard()
    )

@dp.callback_query(F.data.startswith("case_"))
async def case_callback(callback_query: types.CallbackQuery, state: FSMContext):
    case_type = callback_query.data.replace("case_", "")
    case_config = CASES_CONFIG.get(case_type)

    if not case_config:
        await callback_query.answer("❌ Кейс не найден!")
        return

    user = get_user(callback_query.from_user.id)
    if user[3] < case_config['price']:  # Проверка основного баланса
        await callback_query.answer(f"❌ Недостаточно средств! Нужно {case_config['price']} USDT")
        return

    # Списание средств
    update_user_balance(callback_query.from_user.id, -case_config['price'], 'main')

    # Открытие кейса
    item = open_case(case_type, callback_query.from_user.id)

    # Начисление опыта
    add_experience(callback_query.from_user.id, 25)

    rarity_colors = {
        'common': '⚪',
        'rare': '🔵', 
        'legendary': '🟡'
    }

    rarity_emoji = rarity_colors.get(item['rarity'], '⚪')

    result_text = f"""🎉 Кейс {case_config['emoji']} {case_config['name']} открыт!

{rarity_emoji} **{item['name']}**
💰 Стоимость: {item['value']:.2f} USDT
🏷️ Редкость: {item['rarity'].title()}

Предмет добавлен в ваш инвентарь!"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Открыть ещё", callback_data=f"case_{case_type}")],
        [InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inventory")],
        [InlineKeyboardButton(text="◀️ К кейсам", callback_data="cases_menu")]
    ])

    await callback_query.message.edit_text(result_text, reply_markup=keyboard, parse_mode='Markdown')

@dp.callback_query(F.data == "inventory")
async def inventory_callback(callback_query: types.CallbackQuery):
    inventory = get_user_inventory(callback_query.from_user.id)

    if not inventory:
        await callback_query.message.edit_text(
            "🎒 Ваш инвентарь пуст!\n\nОткройте кейсы, чтобы получить предметы.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📦 К кейсам", callback_data="cases_menu")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
            ])
        )
        return

    # Группировка по редкости
    common_items = [item for item in inventory if item['rarity'] == 'common']
    rare_items = [item for item in inventory if item['rarity'] == 'rare'] 
    legendary_items = [item for item in inventory if item['rarity'] == 'legendary']

    total_value = sum(item['value'] for item in inventory)

    inventory_text = f"""🎒 Ваш инвентарь ({len(inventory)} предметов)
💰 Общая стоимость: {total_value:.2f} USDT

"""

    if legendary_items:
        inventory_text += f"🟡 **Легендарные** ({len(legendary_items)}):\n"
        for item in legendary_items[:5]:  # Показываем только первые 5
            inventory_text += f"• {item['name']} - {item['value']:.2f} USDT\n"
        if len(legendary_items) > 5:
            inventory_text += f"... и ещё {len(legendary_items) - 5}\n"
        inventory_text += "\n"

    if rare_items:
        inventory_text += f"🔵 **Редкие** ({len(rare_items)}):\n"
        for item in rare_items[:3]:
            inventory_text += f"• {item['name']} - {item['value']:.2f} USDT\n"
        if len(rare_items) > 3:
            inventory_text += f"... и ещё {len(rare_items) - 3}\n"
        inventory_text += "\n"

    if common_items:
        inventory_text += f"⚪ **Обычные** ({len(common_items)}):\n"
        for item in common_items[:3]:
            inventory_text += f"• {item['name']} - {item['value']:.2f} USDT\n"
        if len(common_items) > 3:
            inventory_text += f"... и ещё {len(common_items) - 3}\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Продать всё", callback_data="sell_all_items")],
        [InlineKeyboardButton(text="📦 К кейсам", callback_data="cases_menu")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])

    await callback_query.message.edit_text(inventory_text, reply_markup=keyboard, parse_mode='Markdown')

@dp.callback_query(F.data == "sell_all_items")
async def sell_all_items_callback(callback_query: types.CallbackQuery):
    inventory = get_user_inventory(callback_query.from_user.id)

    if not inventory:
        await callback_query.answer("❌ Инвентарь пуст!")
        return

    total_value = sum(item['value'] for item in inventory)

    # Начисление средств
    update_user_balance(callback_query.from_user.id, total_value, 'main')

    # Очистка инвентаря
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute("UPDATE users SET inventory = '[]' WHERE user_id = ?", (callback_query.from_user.id,))
    conn.commit()
    conn.close()

    await callback_query.message.edit_text(
        f"✅ Все предметы проданы!\n\n💰 Получено: {total_value:.2f} USDT\nСредства зачислены на основной баланс.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📦 К кейсам", callback_data="cases_menu")],
            [InlineKeyboardButton(text="◀️ Главное меню", callback_data="main_menu")]
        ])
    )

@dp.callback_query(F.data == "profile")
async def profile_callback(callback_query: types.CallbackQuery):
    user = get_user(callback_query.from_user.id)
    if not user:
        return

    level_info = get_user_level_info(callback_query.from_user.id)
    winrate = (user[10] / user[9] * 100) if user[9] > 0 else 0

    # Определение лиги
    if user[8] < 100:
        league = "Bronze 🥉"
    elif user[8] < 1000:
        league = "Silver 🥈"
    elif user[8] < 10000:
        league = "Gold 🥇"
    else:
        league = "Diamond 💎"

    profile_text = f"""👤 Профиль игрока

🆔 ID: `{user[0]}`
👤 Имя: {user[2]}
{'🎮 Username: @' + user[1] if user[1] else ''}

📊 Уровень: {level_info['level']} 
⚡ Опыт: {level_info['experience']}/{level_info['exp_for_next']} ({level_info['progress']:.1f}%)
🏆 Лига: {league}

💰 Балансы:
  • Основной: {user[3]:.2f} USDT
  • Бонусный: {user[4]:.2f} USDT
  • RUSH Coins: {user[5]:,}
  • Bonus Points: {user[6]:,}
  • Loyalty Tokens: {user[7]:,}

🎮 Статистика:
  • Игр сыграно: {user[9]}
  • Побед: {user[10]}
  • Винрейт: {winrate:.1f}%
  • Общий оборот: {user[8]:.2f} USDT

🤝 Рефералы: {user[12]} человек
💸 Доход с рефералов: {user[11]:.2f} USDT

📅 Дата регистрации: {user[14]}"""

    await callback_query.message.edit_text(profile_text, reply_markup=get_profile_keyboard(), parse_mode='Markdown')

@dp.callback_query(F.data == "daily_bonus")
async def daily_bonus_callback(callback_query: types.CallbackQuery):
    if check_daily_bonus(callback_query.from_user.id):
        bonus_info = claim_daily_bonus(callback_query.from_user.id)

        if bonus_info:
            text = f"""🎁 Ежедневный бонус получен!

💎 Бонусный баланс: +{bonus_info['bonus']:.2f} USDT
🪙 RUSH Coins: +{bonus_info['rush_coins']}
🔥 Стрик: {bonus_info['streak']} дней

{'🎉 Недельный бонус! Награды удвоены!' if bonus_info['streak'] >= 7 else ''}

Приходите завтра за новым бонусом!"""
        else:
            text = "❌ Ошибка при получении бонуса!"
    else:
        text = "⏰ Ежедневный бонус уже получен!\n\nПриходите завтра за новым бонусом."

    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="profile")]
        ])
    )

@dp.callback_query(F.data == "promo")
async def promo_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_promo_code)

    await callback_query.message.edit_text(
        """🎯 Введите промокод:

🎁 Активные промокоды:
• WELCOME2024 - 10 USDT бонуса
• RUSH100 - 25 USDT основного баланса  
• CRYPTO50 - 5 USDT бонуса
• VIP2024 - 100 USDT (ограниченное количество)

Введите промокод в следующем сообщении:""",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="profile")]
        ])
    )

@dp.message(StateFilter(UserStates.waiting_promo_code))
async def process_promo_code(message: types.Message, state: FSMContext):
    promo_code = message.text.strip().upper()
    user_id = message.from_user.id

    # Проверка существования промокода
    if promo_code not in PROMO_CODES:
        await message.answer("❌ Промокод не найден!")
        await state.clear()
        return

    # Проверка использования промокода
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute("SELECT * FROM used_promocodes WHERE user_id = ? AND promo_code = ?", (user_id, promo_code))
    used = c.fetchone()

    if used:
        await message.answer("❌ Вы уже использовали этот промокод!")
        conn.close()
        await state.clear()
        return

    promo_info = PROMO_CODES[promo_code]

    # Проверка количества использований
    if promo_info['uses_left'] <= 0:
        await message.answer("❌ Промокод больше не действует!")
        conn.close()
        await state.clear()
        return

    # Активация промокода
    balance_type = promo_info['type']
    bonus_amount = promo_info['bonus']

    update_user_balance(user_id, bonus_amount, balance_type)

    # Запись использования
    c.execute("INSERT INTO used_promocodes (user_id, promo_code, used_date) VALUES (?, ?, ?)",
              (user_id, promo_code, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    # Уменьшение количества использований
    PROMO_CODES[promo_code]['uses_left'] -= 1

    conn.commit()
    conn.close()

    balance_name = "основной" if balance_type == "main" else "бонусный"

    await message.answer(
        f"✅ Промокод активирован!\n\n💰 Получено: {bonus_amount:.2f} USDT на {balance_name} баланс",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
            [InlineKeyboardButton(text="◀️ Главное меню", callback_data="main_menu")]
        ])
    )
    await state.clear()

@dp.callback_query(F.data == "balance")
async def balance_callback(callback_query: types.CallbackQuery):
    user = get_user(callback_query.from_user.id)
    if not user:
        return

    balance_text = f"""💰 Ваши балансы:

💳 Основной баланс: {user[3]:.2f} USDT
🎁 Бонусный баланс: {user[4]:.2f} USDT

🪙 RUSH Coins: {user[5]:,}
⭐ Bonus Points: {user[6]:,}  
🏅 Loyalty Tokens: {user[7]:,}

──────────────────────
💵 Общий баланс: {user[3] + user[4]:.2f} USDT

💡 RUSH Coins - внутриигровая валюта для покупки бустов
⭐ Bonus Points - за выполнение миссий
🏅 Loyalty Tokens - премиум валюта"""

    await callback_query.message.edit_text(balance_text, reply_markup=get_balance_keyboard())

@dp.callback_query(F.data == "deposit")
async def deposit_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_deposit_amount)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 5 USDT", callback_data="quick_deposit_5"),
         InlineKeyboardButton(text="💰 10 USDT", callback_data="quick_deposit_10")],
        [InlineKeyboardButton(text="💰 25 USDT", callback_data="quick_deposit_25"),
         InlineKeyboardButton(text="💰 50 USDT", callback_data="quick_deposit_50")],
        [InlineKeyboardButton(text="💰 100 USDT", callback_data="quick_deposit_100")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="balance")]
    ])

    await callback_query.message.edit_text(
        """💳 Пополнение баланса

Поддерживаемые валюты:
• USDT (Рекомендуется)
• BTC 
• ETH
• TON

💡 Минимальная сумма: 1 USDT
⚡ Мгновенное зачисление через CryptoPay

Выберите сумму или введите свою:""",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("quick_deposit_"))
async def quick_deposit_callback(callback_query: types.CallbackQuery, state: FSMContext):
    amount = float(callback_query.data.split("_")[2])
    await process_deposit_creation(callback_query, amount, state)

async def process_deposit_creation(callback_query, amount, state):
    """Создание депозита"""
    logger.info(f"Creating invoice for user {callback_query.from_user.id} with amount {amount}")
    invoice = await create_invoice(amount)

    if invoice:
        pay_url = invoice.get('pay_url')
        invoice_id = invoice.get('invoice_id')

        await state.update_data(invoice_id=invoice_id, deposit_amount=amount)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=pay_url)],
            [InlineKeyboardButton(text="✅ Проверить оплату", callback_data="check_payment")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="balance")]
        ])

        await callback_query.message.edit_text(
            f"💳 Счёт создан!\n\n💰 К оплате: {amount:.2f} USDT\n🆔 ID счёта: `{invoice_id}`\n\n1️⃣ Нажмите 'Оплатить'\n2️⃣ После оплаты нажмите 'Проверить оплату'",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    else:
        await callback_query.message.edit_text(
            "❌ Ошибка создания счёта!\n\nПопробуйте позже или обратитесь в поддержку.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="deposit")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="balance")]
            ])
        )

@dp.message(StateFilter(UserStates.waiting_deposit_amount))
async def process_deposit_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < 1.0:
            await message.answer("❌ Минимальная сумма: 1 USDT")
            return

        # Создаем callback_query объект для совместимости
        class FakeCallbackQuery:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user

        fake_callback = FakeCallbackQuery(message)
        await process_deposit_creation(fake_callback, amount, state)

    except ValueError:
        await message.answer("❌ Введите корректную сумму!")

@dp.callback_query(F.data == "check_payment")
async def check_payment_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    invoice_id = data.get('invoice_id')
    deposit_amount = data.get('deposit_amount')

    if not invoice_id:
        await callback_query.answer("❌ Счёт не найден!")
        return

    invoice_data = await check_invoice(invoice_id)

    if invoice_data['paid']:
        amount = deposit_amount if deposit_amount else invoice_data['amount']

        # Начисление средств на основной баланс
        update_user_balance(callback_query.from_user.id, amount, 'main')

        # Начисление опыта
        exp_amount = int(amount * 10)  # 10 опыта за каждый USDT
        level_up = add_experience(callback_query.from_user.id, exp_amount)

        # Запись транзакции
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()
        c.execute("INSERT INTO transactions (user_id, amount, currency, type, date, check_id) VALUES (?, ?, ?, ?, ?, ?)",
                  (callback_query.from_user.id, amount, invoice_data['asset'], 'deposit', 
                   datetime.now().strftime("%Y-%m-%d %H:%M:%S"), invoice_id))
        conn.commit()
        conn.close()

        success_text = f"""✅ Пополнение успешно!

💰 Зачислено: {amount:.2f} {invoice_data['asset']}
⚡ Опыт: +{exp_amount}
{'🎉 Повышение уровня!' if level_up else ''}

Средства доступны для игры!"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Играть", callback_data="games_menu")],
            [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
            [InlineKeyboardButton(text="◀️ Главное меню", callback_data="main_menu")]
        ])

        await callback_query.message.edit_text(success_text, reply_markup=keyboard)
        await state.clear()
    else:
        await callback_query.answer("⏳ Платёж не найден. Попробуйте позже.")

# Игровые обработчики
@dp.callback_query(F.data.startswith("game_"))
async def game_callback(callback_query: types.CallbackQuery, state: FSMContext):
    game_type = callback_query.data.replace("game_", "")
    game_config = GAMES_CONFIG.get(game_type)

    if not game_config:
        await callback_query.answer("❌ Игра не найдена!")
        return

    await state.update_data(selected_game=game_type)
    await state.set_state(UserStates.waiting_bet_amount)

    game_info = f"""🎮 {game_config['emoji']} {game_config['name']}

💰 Минимальная ставка: {game_config['min_bet']} USDT
📈 Максимальный множитель: x{game_config['max_multiplier']}

Введите размер ставки:"""

    # Быстрые ставки
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="0.5 USDT", callback_data="quick_bet_0.5"),
         InlineKeyboardButton(text="1 USDT", callback_data="quick_bet_1")],
        [InlineKeyboardButton(text="5 USDT", callback_data="quick_bet_5"),
         InlineKeyboardButton(text="10 USDT", callback_data="quick_bet_10")],
        [InlineKeyboardButton(text="◀️ К играм", callback_data="games_menu")]
    ])

    await callback_query.message.edit_text(game_info, reply_markup=keyboard)

@dp.callback_query(F.data.startswith("quick_bet_"))
async def quick_bet_callback(callback_query: types.CallbackQuery, state: FSMContext):
    bet_amount = float(callback_query.data.split("_")[2])
    await process_game_bet(callback_query, bet_amount, state)

@dp.message(StateFilter(UserStates.waiting_bet_amount))
async def process_bet_amount(message: types.Message, state: FSMContext):
    try:
        bet_amount = float(message.text)

        # Создаем fake callback для совместимости
        class FakeCallbackQuery:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user

        fake_callback = FakeCallbackQuery(message)
        await process_game_bet(fake_callback, bet_amount, state)

    except ValueError:
        await message.answer("❌ Введите корректную сумму!")

async def process_game_bet(callback_query, bet_amount, state):
    """Обработка ставки в игре"""
    data = await state.get_data()
    game_type = data.get('selected_game')
    game_config = GAMES_CONFIG.get(game_type)

    if bet_amount < game_config['min_bet']:
        if hasattr(callback_query, 'answer'):
            await callback_query.answer(f"❌ Минимальная ставка: {game_config['min_bet']} USDT")
        else:
            await callback_query.message.answer(f"❌ Минимальная ставка: {game_config['min_bet']} USDT")
        return

    user = get_user(callback_query.from_user.id)
    if bet_amount > user[3]:  # Проверка основного баланса
        if hasattr(callback_query, 'answer'):
            await callback_query.answer(f"❌ Недостаточно средств! Баланс: {user[3]:.2f} USDT")
        else:
            await callback_query.message.answer(f"❌ Недостаточно средств! Баланс: {user[3]:.2f} USDT")
        return

    # Списание ставки
    update_user_balance(callback_query.from_user.id, -bet_amount, 'main')

    # Выбор игровой логики
    if game_type == 'coin_clash':
        result = play_coin_clash(bet_amount, 'heads')  # Упрощённо
    elif game_type == 'dice_dynasty':
        # Для dice_boosts используем значение по умолчанию, так как колонка может отсутствовать
        user_boosts = 0
        result = play_dice_dynasty(bet_amount, user_boosts)
    elif game_type == 'crash_rocket':
        cash_out = random.uniform(1.1, 5.0) if random.random() < 0.6 else None
        result = play_crash_rocket(bet_amount, cash_out)
    elif game_type == 'slot_legends':
        # Для slot_multiplier используем значение по умолчанию
        user_multiplier = 1.0
        result = play_slot_legends(bet_amount, user_multiplier)
    else:
        # Базовая игровая логика для остальных игр
        win_chance = 0.45
        multiplier = random.uniform(1.5, game_config['max_multiplier'])
        is_win = random.random() < win_chance

        if is_win:
            win_amount = bet_amount * multiplier
            result = {'win': True, 'multiplier': multiplier, 'win_amount': win_amount}
        else:
            result = {'win': False, 'multiplier': 0, 'win_amount': 0}

    # Обработка результата
    if result['win']:
        # Начисление выигрыша
        update_user_balance(callback_query.from_user.id, result['win_amount'], 'main')

        # Обновление статистики
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()
        c.execute("UPDATE users SET total_bets = total_bets + ?, games_played = games_played + 1, wins = wins + 1 WHERE user_id = ?",
                  (bet_amount, callback_query.from_user.id))

        # Реферальный бонус
        c.execute("SELECT referrer_id FROM users WHERE user_id = ?", (callback_query.from_user.id,))
        referrer = c.fetchone()
        if referrer and referrer[0]:
            referral_bonus = result['win_amount'] * 0.25  # 25% с выигрыша
            c.execute("UPDATE users SET referral_earnings = referral_earnings + ?, bonus_balance = bonus_balance + ? WHERE user_id = ?",
                      (referral_bonus, referral_bonus, referrer[0]))

        conn.commit()
        conn.close()

        # Начисление опыта
        exp_amount = int(result['win_amount'] * 5)
        level_up = add_experience(callback_query.from_user.id, exp_amount)

        result_text = f"""🎉 ПОБЕДА!

🎮 {game_config['emoji']} {game_config['name']}
💰 Ставка: {bet_amount:.2f} USDT
📈 Множитель: x{result['multiplier']:.2f}
🏆 Выигрыш: {result['win_amount']:.2f} USDT
⚡ Опыт: +{exp_amount}
{'🎉 Повышение уровня!' if level_up else ''}"""

    else:
        # Обновление статистики
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()
        c.execute("UPDATE users SET total_bets = total_bets + ?, games_played = games_played + 1 WHERE user_id = ?",
                  (bet_amount, callback_query.from_user.id))
        conn.commit()
        conn.close()

        # Начисление опыта за участие
        exp_amount = 5
        add_experience(callback_query.from_user.id, exp_amount)

        result_text = f"""😞 Поражение

🎮 {game_config['emoji']} {game_config['name']}
💰 Ставка: {bet_amount:.2f} USDT
💸 Потеряно: {bet_amount:.2f} USDT
⚡ Опыт: +{exp_amount}"""

    # Запись игры в БД
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute("INSERT INTO games (user_id, game_type, bet_amount, win_amount, result, multiplier, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (callback_query.from_user.id, game_type, bet_amount, result.get('win_amount', 0), 
               'win' if result['win'] else 'loss', result.get('multiplier', 0), 
               datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    # Публикация в канал
    await publish_bet_result_to_channel(
        callback_query.from_user.id,
        callback_query.from_user.username,
        game_config['name'],
        bet_amount,
        result
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Играть ещё", callback_data=f"game_{game_type}")],
        [InlineKeyboardButton(text="🎮 Другая игра", callback_data="games_menu")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="main_menu")]
    ])

    if hasattr(callback_query, 'message'):
        await callback_query.message.edit_text(result_text, reply_markup=keyboard)
    else:
        await callback_query.message.answer(result_text, reply_markup=keyboard)

    await state.clear()

# Публикация в канал
async def publish_bet_result_to_channel(user_id, username, game_name, bet_amount, result):
    """Публикация результата ставки в канал"""
    username_display = f"@{username}" if username else "Анонимный игрок"

    if result['win']:
        emoji = "🎉"
        status = "ПОБЕДА"
        amount_text = f"💰 Выигрыш: {result['win_amount']:.2f} USDT (x{result['multiplier']:.2f})"
    else:
        emoji = "😞"
        status = "ПОРАЖЕНИЕ"
        amount_text = f"💸 Потеряно: {bet_amount:.2f} USDT"

    text = f"""{emoji} {status} | {username_display}

🎮 Игра: {game_name}
💰 Ставка: {bet_amount:.2f} USDT
{amount_text}

[🎮 Играть](https://t.me/CryptoRushCazino_Bot) | [📦 Кейсы](https://t.me/CryptoRushCazino_Bot?start=cases) | [🤝 Рефералы](https://t.me/CryptoRushCazino_Bot?start=ref)"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Сделать ставку", url="https://t.me/CryptoRushCazino_Bot")],
        [InlineKeyboardButton(text="📦 Открыть кейс", url="https://t.me/CryptoRushCazino_Bot?start=cases")]
    ])

    try:
        await bot.send_message(BETS_CHANNEL_ID, text, reply_markup=keyboard, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error publishing to channel: {e}")

# Реферальная система
@dp.callback_query(F.data == "referral")
async def referral_callback(callback_query: types.CallbackQuery):
    user = get_user(callback_query.from_user.id)
    if not user:
        return

    level_info = get_user_level_info(callback_query.from_user.id)

    # Определение процента комиссии по уровню
    if level_info['level'] < 5:
        ref_percent = "25% / 10% / 5%"
    elif level_info['level'] < 15:
        ref_percent = "30% / 12% / 6%"
    else:
        ref_percent = "35% / 15% / 7%"

    referral_text = f"""🤝 Трёхуровневая реферальная система

💸 Ваши проценты: {ref_percent}
• 1-й уровень: С прямых рефералов
• 2-й уровень: С рефералов ваших рефералов  
• 3-й уровень: С рефералов 2-го уровня

📊 Статистика:
┏👥 Рефералов: {user[12]} человек
┣💰 Заработано: {user[11]:.2f} USDT
┣🏆 Ваш уровень: {level_info['level']}
┗⚡ Ваша ссылка: `{user[13]}`

🎁 Бонусы:
• Новый реферал: +5 USDT бонуса
• 25% с выигрышей рефералов 1-го уровня
• 10% с выигрышей рефералов 2-го уровня
• 5% с выигрышей рефералов 3-го уровня

💡 Приглашайте друзей и зарабатывайте пассивно!"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Копировать ссылку", callback_data="copy_ref_link")],
        [InlineKeyboardButton(text="📊 Детальная статистика", callback_data="ref_stats")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])

    await callback_query.message.edit_text(referral_text, reply_markup=keyboard, parse_mode='Markdown')

@dp.callback_query(F.data == "copy_ref_link")
async def copy_ref_link_callback(callback_query: types.CallbackQuery):
    user = get_user(callback_query.from_user.id)
    if user:
        await callback_query.answer(f"📋 Ссылка скопирована!\n{user[13]}", show_alert=True)

# Админские команды
def is_admin(username):
    return username in ADMIN_USERNAMES

@dp.message(Command("admin"))
async def admin_panel_command(message: types.Message):
    if not is_admin(message.from_user.username):
        return

    conn = sqlite3.connect('casino.db')
    c = conn.cursor()

    # Статистика
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]

    c.execute("SELECT SUM(total_bets), SUM(balance), SUM(bonus_balance) FROM users")
    stats = c.fetchone()
    total_bets, total_balance, total_bonus = stats

    c.execute("SELECT COUNT(*) FROM games")
    total_games = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM transactions WHERE type = 'deposit'")
    total_deposits = c.fetchone()[0]

    conn.close()

    admin_text = f"""👑 Панель администратора

📊 Общая статистика:
👥 Пользователей: {total_users}
🎮 Игр сыграно: {total_games}
💳 Депозитов: {total_deposits}
💰 Общий оборот: {total_bets or 0:.2f} USDT
💵 Балансы игроков: {(total_balance or 0) + (total_bonus or 0):.2f} USDT

🛠️ Доступные команды:
/stats - Детальная статистика
/top_players - Топ игроков
/add_bonus @username сумма - Добавить бонус
/broadcast текст - Рассылка"""

    await message.answer(admin_text)

@dp.message(Command("stats"))
async def stats_command(message: types.Message):
    if not is_admin(message.from_user.username):
        return

    conn = sqlite3.connect('casino.db')
    c = conn.cursor()

    # Статистика по играм
    c.execute("SELECT game_type, COUNT(*), SUM(bet_amount), SUM(win_amount) FROM games GROUP BY game_type")
    game_stats = c.fetchall()

    # Статистика по дням
    c.execute("SELECT DATE(date), COUNT(*), SUM(bet_amount) FROM games WHERE date >= date('now', '-7 days') GROUP BY DATE(date)")
    daily_stats = c.fetchall()

    conn.close()

    stats_text = "📊 Детальная статистика\n\n🎮 По играм:\n"
    for game_type, count, total_bet, total_win in game_stats:
        house_edge = ((total_bet - total_win) / total_bet * 100) if total_bet > 0 else 0
        stats_text += f"• {game_type}: {count} игр, оборот {total_bet:.2f} USDT, доходность {house_edge:.1f}%\n"

    stats_text += "\n📅 За последние 7 дней:\n"
    for date, count, total_bet in daily_stats:
        stats_text += f"• {date}: {count} игр, {total_bet:.2f} USDT\n"

    await message.answer(stats_text)

# Поддержка и прочие функции
@dp.callback_query(F.data == "support")
async def support_callback(callback_query: types.CallbackQuery):
    support_text = f"""💬 Служба поддержки

👤 Администратор: {SUPPORT_USERNAME}
🕐 Время работы: 10:00 - 22:00 (МСК)

📋 Частые вопросы:

❓ Как пополнить баланс?
Нажмите 'Профиль' → 'Баланс' → 'Пополнить'

❓ Как работают кейсы?
Покупайте кейсы и получайте случайные предметы разной редкости

❓ Как работает реферальная система?
Приглашайте друзей по своей ссылке и получайте % с их выигрышей

❓ Проблемы с выводом?
Обратитесь к администратору с указанием суммы и времени

🔗 Полезные ссылки:
📢 Канал: {CASINO_CHANNEL_URL}
🗞️ Новости: {NEWS_CHANNEL_URL}"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать в поддержку", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])

    await callback_query.message.edit_text(support_text, reply_markup=keyboard)

# Обработчики для нереализованных функций
@dp.callback_query(F.data.in_(["withdraw", "exchange", "premium", "tournaments", "missions", "achievements", "stats", "ref_stats"]))
async def not_implemented_callback(callback_query: types.CallbackQuery):
    feature_names = {
        "withdraw": "Вывод средств",
        "exchange": "Обмен валют", 
        "premium": "Премиум подписка",
        "tournaments": "Турниры",
        "missions": "Система миссий",
        "achievements": "Достижения",
        "stats": "Детальная статистика",
        "ref_stats": "Статистика рефералов"
    }

    feature_name = feature_names.get(callback_query.data, "Данная функция")

    await callback_query.answer(f"⏳ {feature_name} находится в разработке!", show_alert=True)

# Middleware для проверки подписки
@dp.message()
async def check_subscription_middleware(message: types.Message):
    if not await check_subscription(message.from_user.id):
        await message.answer(
            "🔒 Для использования бота обязательно быть подписанным на канал!",
            reply_markup=get_subscription_keyboard()
        )
        return

@dp.callback_query()
async def check_subscription_middleware_callback(callback_query: types.CallbackQuery):
    if callback_query.data != "check_subscription" and not await check_subscription(callback_query.from_user.id):
        await callback_query.message.edit_text(
            "🔒 Для использования бота обязательно быть подписанным на канал!",
            reply_markup=get_subscription_keyboard()
        )
        return

# Главная функция
async def main():
    init_db()
    logger.info("🚀 Crypto Rush Casino бот запускается...")

    # Запуск Flask веб-приложения в отдельном потоке
    import threading
    from web_app import app as flask_app

    def run_flask():
        flask_app.run(host='0.0.0.0', port=5000, debug=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("🌐 Веб-приложение запущено на порту 5000")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
