# 🔐 PERSONAL VAULT

Личное защищённое облако. Flask backend + sci-fi UI.

## Структура проекта
```
vault/
├── app.py              # Flask сервер
├── static/
│   └── index.html      # Весь фронтенд
├── uploads/            # Файлы (создаётся автоматически)
├── requirements.txt
├── Procfile            # Для Railway
└── .env.example        # Пример переменных
```

## 🚀 Деплой на Railway (бесплатно)

### Шаг 1 — GitHub
1. Создай аккаунт на github.com
2. Создай новый репозиторий (назови `personal-vault`)
3. Загрузи все файлы проекта

```bash
git init
git add .
git commit -m "Initial vault"
git remote add origin https://github.com/ТВОЙ_ЮЗЕРНЕЙМ/personal-vault.git
git push -u origin main
```

### Шаг 2 — Railway
1. Зайди на railway.app
2. Нажми "New Project" → "Deploy from GitHub repo"
3. Выбери репозиторий `personal-vault`
4. Railway автоматически задеплоит!

### Шаг 3 — Переменные окружения
В Railway → твой проект → Variables → добавь:

| Ключ | Значение |
|------|---------|
| `VAULT_USER` | твой логин |
| `VAULT_PASS` | твой пароль |
| `SECRET_KEY` | случайная строка |

### Шаг 4 — Домен
Railway → Settings → Generate Domain → получишь ссылку типа:
`https://personal-vault-xxxx.railway.app`

Открывай с любого устройства! 🎉

---

## 💻 Локальный запуск

```bash
pip install -r requirements.txt
python app.py
```
Открой: http://localhost:5000

---

## 🔐 Безопасность
- Логин: `NASA` (меняй в переменных)
- Пароль: `jarvis2026` (меняй в переменных!)
- 3 неверных попытки = все файлы удаляются автоматически
- Сессия через cookie
