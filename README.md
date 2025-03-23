# 🤖 Discord Event Bot for NSYSU

This is a custom Discord bot designed to help students **organize and join self-hosted events** within a Discord server. It also includes a feature that **automatically fetches the latest announcements** from National Sun Yat-sen University (NSYSU)'s official website.

---

## 🎯 Features

- 📅 **Event Management**
  - Create new events
  - Register participants
  - View available upcoming events
- 📰 **Auto Announcement Fetching**
  - Periodically crawls the NSYSU website for new announcements
  - Sends updates to a specific Discord channel
- 🔒 Role-restricted command access (e.g., only admins can publish events)

---

## 🛠 Tech Stack

- **Language**: Python
- **Libraries**:
  - `discord.py` – for building the bot and handling Discord events
  - `requests`, `BeautifulSoup` – for web scraping NSYSU announcements
  - `apscheduler` – for periodic tasks
- **Deployment**: Runs on a cloud VM or local server with a long-running script

---

## 🚀 Getting Started

