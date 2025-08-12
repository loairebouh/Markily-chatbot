# 🏦 Markily - Telegram Debt & Loan Manager Bot

A smart Telegram bot that helps you track money you lend to and borrow from friends and family. Never forget who owes what again!

## ✨ Features

### 💰 Smart Balance Tracking

- **Net balance calculation** - automatically calculates who owes whom
- **Multi-currency support** - DZD, USD, EUR with smart defaults
- **Real-time updates** - see updated balances after each transaction

### 👥 Contact Management

- **Fuzzy search** - find contacts with partial names (e.g., "ami" finds "Amine")
- **Auto-add contacts** - suggests adding new contacts during transactions
- **Contact overview** - see all contacts with their current balance status

### 📊 Transaction History

- **Complete audit trail** - every transaction with timestamps and notes
- **Rich formatting** - clear visual distinction between lending and borrowing
- **Detailed notes** - remember why money was exchanged

### 🔄 Easy Balance Clearing

- **Smart clearing** - automatically determines payment direction
- **Partial payments** - clear balances partially or completely
- **Settlement tracking** - know when you're even with someone

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Telegram account
- Bot token from [@BotFather](https://t.me/botfather)

### Installation

1. **Create Virtual Environment**

   ```bash
   python3 -m venv markily_env
   source markily_env/bin/activate  # On Windows: markily_env\Scripts\activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Get your bot token**

   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Use `/newbot` command and follow instructions
   - Copy your bot token

4. **Configure the bot**

   ```bash
   # Create .env file with your bot token
   echo "BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ" > .env
   ```

5. **Run the bot**

   ```bash
   # Option 1: Use the startup script
   ./start_bot.sh

   # Option 2: Run manually
   source markily_env/bin/activate
   python markily_bot.py
   ```

## 📱 Usage Examples

```bash
# Add a contact
/addcontact Amine Khoudor +213123456789

# Record transactions
/lend amine 1000 DZD lunch money
/borrow sara 2000 DZD taxi fare
/lend john 50 USD dinner

# Check balances
/balance amine
# → "Amine Khoudor owes you 1000 DZD"

# View history
/history amine
# → Shows complete transaction timeline

# Clear balances
/clear amine 1000 DZD final payment
# → "You and Amine Khoudor are now settled! 🎉"
```

## 📋 Commands Reference

| Command       | Description                     | Example                            |
| ------------- | ------------------------------- | ---------------------------------- |
| `/start`      | Welcome message and overview    | `/start`                           |
| `/help`       | Detailed command guide          | `/help`                            |
| `/addcontact` | Add new contact                 | `/addcontact John Doe +1234567890` |
| `/contacts`   | List all contacts with balances | `/contacts`                        |
| `/lend`       | Record money you lent           | `/lend john 100 USD dinner`        |
| `/borrow`     | Record money you borrowed       | `/borrow sara 50 EUR gas`          |
| `/balance`    | Check balance with someone      | `/balance john`                    |
| `/history`    | View transaction history        | `/history sara`                    |
| `/clear`      | Clear/reduce balance            | `/clear john 100 USD payment`      |

## 🏗️ Architecture

### Database Schema

- **Users**: Telegram user information
- **Contacts**: Your personal contacts with optional phone numbers
- **Transactions**: All lending/borrowing records with notes and timestamps

### Key Features

- **SQLite database** - lightweight, no setup required
- **Fuzzy search** - find contacts even with typos
- **Net balance calculation** - smart math handles complex scenarios
- **Rich UI** - emojis and formatting for better UX
- **Error handling** - helpful messages guide users

## 🌟 Use Cases

### Personal Finance

- Track money lent to friends and family
- Remember informal loans and IOUs
- Keep receipts for group expenses
- Manage small business cash flows

### Group Activities

- Split restaurant bills
- Share vacation expenses
- Track group purchases
- Manage household expenses

## 🛡️ Privacy & Security

- **Local storage** - all data stored locally in SQLite
- **No cloud sync** - your financial data never leaves your server
- **Telegram security** - encrypted communication via Telegram API
- **Contact privacy** - only you can see your contacts and transactions

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### 🐛 Bug Reports

- Use GitHub Issues to report bugs
- Include steps to reproduce
- Mention your Python and OS version

### 💡 Feature Requests

- Suggest new features via GitHub Issues
- Explain your use case
- Consider backward compatibility

### 🔧 Development Setup

```bash
git clone https://github.com/yourusername/markily-telegram-bot.git
cd markily-telegram-bot
pip install -r requirements.txt
# Create your bot token and test locally
```

### 📝 Pull Request Guidelines

- Fork the repository
- Create a feature branch
- Write tests for new features
- Update documentation
- Submit PR with clear description

## 📊 Roadmap

### Version 2.0

- [ ] Multi-user support (family/group accounts)
- [ ] Export transactions to CSV/Excel
- [ ] Recurring transaction reminders
- [ ] Currency conversion rates
- [ ] Photo receipts with OCR

### Version 2.1

- [ ] Web dashboard interface
- [ ] Integration with banking APIs
- [ ] Advanced reporting and analytics
- [ ] Backup and restore functionality

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

[![GitHub stars](https://img.shields.io/github/stars/yourusername/markily-telegram-bot.svg?style=social)](https://github.com/yourusername/markily-telegram-bot/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/yourusername/markily-telegram-bot.svg?style=social)](https://github.com/yourusername/markily-telegram-bot/network/members)
[![GitHub issues](https://img.shields.io/github/issues/yourusername/markily-telegram-bot.svg)](https://github.com/yourusername/markily-telegram-bot/issues)
[![Apache License 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

## 🙏 Acknowledgments

- Built with [python-telegram-bot](https://python-telegram-bot.org/)
- Inspired by the need to track informal loans between friends
- Thanks to the open-source community for tools and libraries
- **Special thanks to Abdallah Mehiz** — for his invaluable support and for inspiring the idea to make this app as a Telegram bot


