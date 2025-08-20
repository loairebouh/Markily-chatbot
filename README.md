# 🏦 Markily - Telegram Debt Tracker Bot

A simple Telegram bot to track money you lend and borrow — with a clean button interface.  

---

## 🚀 Quick Setup

### 1. Get a Bot Token  
- Message [@BotFather](https://t.me/botfather) → `/newbot`  
- Copy your new bot token  

### 2. Local Setup (TypeScript)  

```bash
git clone <repo-url>
cd markily-chatbot
npm install
echo "BOT_TOKEN=your_token_here" > .env
npm run dev 
```

3. Docker Setup

```bash
docker compose up -d
``` 

✨ Features

    💰 Track lending & borrowing

    👤 Contact management

    📊 Balance summaries & history

    ✅ Clear balances

    🗃️ SQLite database with notes

🎮 Usage

Start the bot with /start, then use the buttons:

    💸 I Lent Money / 💰 I Borrowed Money

    👤 Add Contact / 🗑️ Delete Contact

    📊 View Balances / 📜 History

    ✅ Clear Balance

📦 Deployment

Copy .env.example → .env with your bot token, then run:

docker compose up -d --build

📄 License

This project is licensed under the MIT License — see the LICENSE

file for details.
🙏 Acknowledgments

    Built with Telegraf

    Inspired by the need to track informal loans

    Special thanks to Abdallah Mehiz for support and inspiration


