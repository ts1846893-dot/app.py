
from flask import Flask, render_template_string, jsonify
import sqlite3
import json

app = Flask(__name__)

# HTML шаблон для веб-приложения
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Rush Casino</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        
        .container {
            text-align: center;
            max-width: 800px;
            padding: 2rem;
        }
        
        h1 {
            font-size: 3rem;
            margin-bottom: 1rem;
            background: linear-gradient(45deg, #00f5ff, #ff6b6b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            font-size: 1.2rem;
            margin-bottom: 2rem;
            opacity: 0.8;
        }
        
        .games-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }
        
        .game-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 1.5rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease;
        }
        
        .game-card:hover {
            transform: translateY(-5px);
        }
        
        .game-emoji {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .game-name {
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        
        .game-desc {
            font-size: 0.9rem;
            opacity: 0.7;
        }
        
        .cta-button {
            display: inline-block;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            color: white;
            text-decoration: none;
            padding: 1rem 2rem;
            border-radius: 50px;
            font-weight: bold;
            margin: 1rem;
            transition: transform 0.3s ease;
        }
        
        .cta-button:hover {
            transform: scale(1.05);
        }
        
        .stats {
            display: flex;
            justify-content: space-around;
            margin: 2rem 0;
            flex-wrap: wrap;
        }
        
        .stat-item {
            text-align: center;
            margin: 0.5rem;
        }
        
        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #00f5ff;
        }
        
        .stat-label {
            opacity: 0.7;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎰 Crypto Rush Casino</h1>
        <p class="subtitle">Ваше криптовалютное казино с уникальными играми</p>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number" id="users-count">{{ stats.users }}</div>
                <div class="stat-label">Игроков</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="games-count">{{ stats.games }}</div>
                <div class="stat-label">Игр сыграно</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">${{ stats.volume }}</div>
                <div class="stat-label">Оборот USDT</div>
            </div>
        </div>
        
        <div class="games-grid">
            <div class="game-card">
                <div class="game-emoji">🪙</div>
                <div class="game-name">Coin Clash</div>
                <div class="game-desc">PvP орёл/решка с live-соперником</div>
            </div>
            <div class="game-card">
                <div class="game-emoji">🎲</div>
                <div class="game-name">Dice Dynasty</div>
                <div class="game-desc">Прокачиваемые кости с бустами</div>
            </div>
            <div class="game-card">
                <div class="game-emoji">🚀</div>
                <div class="game-name">Crash Rocket</div>
                <div class="game-desc">Космический корабль до x100</div>
            </div>
            <div class="game-card">
                <div class="game-emoji">🎰</div>
                <div class="game-name">Slot Legends</div>
                <div class="game-desc">Слоты с легендарными джекпотами</div>
            </div>
            <div class="game-card">
                <div class="game-emoji">📦</div>
                <div class="game-name">CS:GO Кейсы</div>
                <div class="game-desc">Откройте редкие скины</div>
            </div>
            <div class="game-card">
                <div class="game-emoji">🎯</div>
                <div class="game-name">Roulette Rush</div>
                <div class="game-desc">Молниеносная рулетка</div>
            </div>
        </div>
        
        <a href="https://t.me/CryptoRushCazino_Bot" class="cta-button">
            🎮 Играть в Telegram
        </a>
        
        <a href="https://t.me/cryptorush_24_7" class="cta-button">
            📢 Наш канал
        </a>
    </div>
    
    <script>
        // Анимация счетчиков
        function animateCount(element, target) {
            let count = 0;
            const increment = target / 100;
            const timer = setInterval(() => {
                count += increment;
                if (count >= target) {
                    element.textContent = Math.floor(target);
                    clearInterval(timer);
                } else {
                    element.textContent = Math.floor(count);
                }
            }, 20);
        }
        
        // Загрузка статистики
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                animateCount(document.getElementById('users-count'), data.users);
                animateCount(document.getElementById('games-count'), data.games);
            })
            .catch(console.error);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Главная страница веб-приложения"""
    try:
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()
        
        # Получаем статистику
        c.execute("SELECT COUNT(*) FROM users")
        users_count = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM games")
        games_count = c.fetchone()[0] or 0
        
        c.execute("SELECT SUM(total_bets) FROM users")
        total_volume = c.fetchone()[0] or 0
        
        conn.close()
        
        stats = {
            'users': users_count,
            'games': games_count,
            'volume': f"{total_volume:.0f}"
        }
        
    except Exception as e:
        print(f"Database error: {e}")
        stats = {'users': 0, 'games': 0, 'volume': '0'}
    
    return render_template_string(HTML_TEMPLATE, stats=stats)

@app.route('/api/stats')
def api_stats():
    """API для получения статистики"""
    try:
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM users")
        users_count = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM games")
        games_count = c.fetchone()[0] or 0
        
        c.execute("SELECT SUM(total_bets) FROM users")
        total_volume = c.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'users': users_count,
            'games': games_count,
            'volume': total_volume or 0
        })
        
    except Exception as e:
        print(f"API stats error: {e}")
        return jsonify({'users': 0, 'games': 0, 'volume': 0})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
