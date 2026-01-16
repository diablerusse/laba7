<div align="center">

  # 📨 Mail Ticket System (Lab 7)
  
  **Распределенная система обработки почтовых заявок на Python**

  ![Python Version](https://img.shields.io/badge/Python-3.14-blue?style=for-the-badge&logo=python)
  ![Protocol](https://img.shields.io/badge/Protocol-TCP%20%7C%20SMTP%20%7C%20IMAP-orange?style=for-the-badge)
  ![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

  <p align="center">
    <i>Учебный проект, реализующий полный цикл обработки тикетов: от отправки запроса через сокеты до мониторинга почтового ящика и логирования.</i>
  </p>

</div>

---

## 🏗 Архитектура проекта

Система состоит из трех независимых модулей, взаимодействующих друг с другом:

```mermaid
graph LR
  A[Client] -- Socket/JSON --> B[Server]
  B -- SMTP --> C((Email Server))
  D[Collector] -- IMAP --> C
  D -- Write --> E[Logs]
