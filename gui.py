# 📤 Инструкция: Загрузка проекта на GitHub

Пошаговая инструкция для загрузки `yandex-ai-checker` на GitHub с нуля.

---

## Шаг 1. Установить Git

### Windows
Скачайте и установите с официального сайта:
👉 https://git-scm.com/download/win

Во время установки оставьте все настройки по умолчанию.

### macOS
```bash
brew install git
```

### Linux (Ubuntu/Debian)
```bash
sudo apt install git
```

Проверьте установку:
```bash
git --version
# git version 2.x.x
```

---

## Шаг 2. Настроить Git (один раз)

```bash
git config --global user.name "Ваше Имя"
git config --global user.email "ваш@email.com"
```

---

## Шаг 3. Создать аккаунт на GitHub

Если у вас ещё нет аккаунта:
👉 https://github.com/signup

---

## Шаг 4. Создать репозиторий на GitHub

1. Войдите на https://github.com
2. Нажмите кнопку **"New"** (зелёная, сверху слева) или перейдите на:
   👉 https://github.com/new
3. Заполните форму:
   - **Repository name:** `yandex-ai-checker`
   - **Description:** `Проверка блока Алисы AI в поисковой выдаче Яндекса`
   - **Visibility:** Public (или Private — на ваш выбор)
   - **НЕ ставьте** галочки "Add README", "Add .gitignore" (они уже есть в проекте)
4. Нажмите **"Create repository"**

После создания GitHub покажет страницу с инструкциями — не закрывайте её.

---

## Шаг 5. Подготовить проект локально

Откройте терминал (или командную строку) и перейдите в папку проекта:

```bash
cd путь/до/yandex-ai-checker
```

Например:
```bash
cd C:\Projects\yandex-ai-checker     # Windows
cd ~/Projects/yandex-ai-checker      # macOS/Linux
```

---

## Шаг 6. Инициализировать Git в проекте

```bash
# Инициализируем репозиторий
git init

# Добавляем все файлы
git add .

# Делаем первый коммит
git commit -m "feat: initial release — Yandex AI Checker with GUI"
```

---

## Шаг 7. Привязать к GitHub и загрузить

Скопируйте ссылку вашего репозитория с GitHub (она выглядит так):
`https://github.com/ВАШ_ЛОГИН/yandex-ai-checker.git`

```bash
# Привязываем удалённый репозиторий
git remote add origin https://github.com/ВАШ_ЛОГИН/yandex-ai-checker.git

# Переименовываем ветку в main (современный стандарт)
git branch -M main

# Загружаем на GitHub
git push -u origin main
```

При первом push Git попросит авторизоваться:
- **Логин:** ваш GitHub username
- **Пароль:** Personal Access Token (не пароль от аккаунта!)

### Как получить Personal Access Token
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token (classic)
3. Название: `git-push`
4. Срок: 90 дней
5. Поставьте галочку **`repo`**
6. Нажмите Generate token — **скопируйте токен сразу**, он показывается один раз!

---

## Шаг 8. Проверить результат

Откройте ваш репозиторий в браузере:
```
https://github.com/ВАШ_ЛОГИН/yandex-ai-checker
```

Вы должны увидеть все файлы проекта и красивый README.

---

## 🔄 Как загружать изменения в будущем

После любых правок в коде:

```bash
git add .
git commit -m "fix: описание что изменили"
git push
```

---

## 💡 Полезные команды Git

```bash
git status              # что изменилось
git log --oneline       # история коммитов
git diff                # детали изменений
git pull                # получить обновления с GitHub
```

---

## ❓ Частые проблемы

### "Permission denied" при push
→ Убедитесь, что используете Personal Access Token (не пароль), и он имеет права `repo`.

### "src refspec main does not match any"
→ Сначала сделайте `git commit`, потом `git push`.

### "remote origin already exists"
→ Выполните: `git remote set-url origin https://github.com/ВАШ_ЛОГИН/yandex-ai-checker.git`

### Файл `output/result.xlsx` попал в репозиторий
→ Он добавлен в `.gitignore`, поэтому не должен. Если попал:
```bash
git rm --cached output/result.xlsx
git commit -m "chore: remove result from tracking"
```
