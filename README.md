# 🏦 Markily - Telegram Debt Tracker Bot

A Telegram bot with button interface to track money you lend and borrow. Never forget who owes what again!

## � Quick Setup

1. **Get Bot Token**
   - Message [@BotFather](https://t.me/botfather) → `/newbot`

2. **Local Setup**
   ```bash
   git clone <repo-url>
   cd markily-telegram-chatbot
   pip install -r requirements.txt
   echo "BOT_TOKEN=your_token_here" > .env
   python markily_bot.py
   ```

3. **Docker Setup**
   ```bash
   docker compose up -d
   ```

## ✨ Features

- 💰 Track lending/borrowing with button interface
- � Contact management 
- 📊 Balance summaries and transaction history
- ✅ Clear balances and delete contacts
- 🗃️ SQLite database with notes

## 🎮 How to Use

Start the bot with `/start` and use the buttons:
- **💸 I Lent Money** / **💰 I Borrowed Money**
- **👤 Add Contact** / **🗑️ Delete Contact** 
- **📊 View Balances** / **📜 Transaction History**
- **✅ Clear Balance**

## � Deployment

Copy `.env.example` to `.env` with your bot token, then:

```bash
# Local
docker compose up -d

# VPS
git clone <repo> && cd markily-telegram-chatbot
docker compose up -d --build
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [python-telegram-bot](https://python-telegram-bot.org/)
- Inspired by the need to track informal loans between friends
- Thanks to the open-source community for tools and libraries

## 💬 Support

- **Issues**: Use GitHub Issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Telegram**: Join our support group [@MarkilySupport](https://t.me/MarkilySupport)

---

**Made with ❤️ for people who lend money to friends and actually want to keep track of it.**

