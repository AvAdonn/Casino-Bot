# 🎰 Async Telegram Casino Backend

A high-performance, asynchronous Telegram bot providing a fully functional casino-style gaming ecosystem. Built with a focus on fault tolerance, transactional safety, and scalable architecture.

## 📸 Previews

*(Replace the paths below with your actual images once uploaded to the repository)*

![Main Menu & Navigation](assets/main_menu.png)
*Interactive UI with dynamic keyboard generation*

![Gameplay & Mechanics](assets/gameplay.png)
*FSM-based game loops using Telegram native dice mechanics*

![Admin Panel & Payments](assets/admin_panel.png)
*Secure withdrawal processing and deposit management*

## ✨ Core Architecture & Features

Unlike standard bots, this project is engineered to handle concurrent users and financial integrity safely:
* **Financial Transaction Safety:** Engineered with Pessimistic Locking (`with_for_update`) via SQLAlchemy to completely eliminate Race Conditions during concurrent betting.
* **Robust State Management:** Implemented complex FSM (Finite State Machine) to handle seamless multi-step user interactions (e.g., betting, gameplay loops).
* **Payment Gateway Integration:** Modular system for processing deposits and handling withdrawal requests securely.
* **Admin Dashboard:** Secure interface for reviewing and approving financial transactions.
* **Separation of Concerns:** Business logic is strictly separated from UI text (Lexicon pattern) to ensure maintainability.

## 🛠 Tech Stack

* **Language:** Python 3.11+
* **Framework:** aiogram 3.x (Asyncio)
* **Database:** PostgreSQL / SQLite + SQLAlchemy 2.0 (Async Engine)
* **Architecture Patterns:** FSM, Dependency Injection (via Middleware), Lexicon Pattern.

## 📂 Project Structure

```text
src/casino_bot/
├── database/     # ORM models and database connection logic
├── handlers/     # Request routing and business logic execution
├── keyboards/    # Dynamic Inline/Reply keyboard builders
├── middleware/   # User authentication and database session injection
├── services/     # Core game engine and mathematical logic
├── __main__.py   # Application entry point
├── callback.py   # Callback data factories
└── fsm.py        # State machine definitions
```

## 🚀 Getting Started
**Clone the repository:**
```
git clone [https://github.com/AvAdonn/Casino-Bot.git](https://github.com/AvAdonn/Casino-Bot.git)
```
```
cd Casino-Bot
```
**Install dependencies:**
```
pip install -e .
```
**Configure environment variables:**

Create a .env file in the root directory and add your secure credentials:
```
BOT_TOKEN=your_bot_token_here
DB_URL=sqlite+aiosqlite:///database.db
#Add any other required variables (e.g., Admin IDs, Payment Tokens)
```
**Run the application:**
```
python -m src.casino_bot
```
👨‍💻 Author
Nazarii Stoliar

GitHub Profile
