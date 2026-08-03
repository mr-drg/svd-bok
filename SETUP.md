# Настройка публикации на GitHub Pages (разово)

Эти шаги делает пользователь сам — агент не создаёт аккаунты и не работает
с паролями/токенами в чате.

## 1. Аккаунт GitHub

Если аккаунта ещё нет — зарегистрируйся на https://github.com (бесплатный
план полностью достаточен).

## 2. Создать пустой репозиторий

На https://github.com/new:
- Repository name: `quatz-site` (или другое — но тогда поправь `baseUrl`
  в `quartz.config.yaml` и команду `git remote add` ниже).
- Public.
- **Не** добавлять README/gitignore/license — репозиторий уже наполнен
  локально, ты просто подключишь существующую папку.

## 3. Настроить git-аутентификацию на этой машине

Один из вариантов:
- **SSH-ключ**: `ssh-keygen -t ed25519 -C "твой-email"`, затем добавить
  публичный ключ (`~/.ssh/id_ed25519.pub`) в
  https://github.com/settings/keys.
- **HTTPS + Personal Access Token**: создать токен на
  https://github.com/settings/tokens, при первом `git push` ввести его
  вместо пароля — macOS Keychain (`git config --global credential.helper
  osxkeychain`) запомнит его сам.

Агент не должен видеть и не запрашивает сам токен/пароль — вводишь их
только в системный диалог/терминал напрямую.

## 4. Подключить локальный репозиторий

```bash
cd ~/Sites/quatz-site
git remote add origin git@github.com:<твой-логин>/quatz-site.git
# либо через HTTPS:
# git remote add origin https://github.com/<твой-логин>/quatz-site.git
git add -A
git commit -m "init: quatz-site scaffold"
git push -u origin main
```

## 5. Включить GitHub Pages

В репозитории на GitHub: Settings → Pages → Source → **GitHub Actions**.
Workflow `.github/workflows/deploy.yml` уже в репозитории — он соберёт
сайт (`npx quartz build`) и задеплоит на Pages при каждом push в `main`.

## 6. Поправить `baseUrl`

В `quartz.config.yaml` замени плейсхолдер:

```yaml
baseUrl: PLACEHOLDER-USERNAME.github.io/quatz-site
```

на реальный:

```yaml
baseUrl: <твой-логин>.github.io/quatz-site
```

Закоммить и запушить — иначе внутренние ссылки/RSS/og-превью будут
указывать на плейсхолдер.

## 7. Заголовок сайта

В `quartz.config.yaml` замени:

```yaml
pageTitle: "TODO: выбери заголовок сайта (экспертное позиционирование, без TS Solution)"
```

на финальный заголовок сайта.

## Дальше

С этого момента публикация — через ежедневный ритуал (скилл
`quatz-publish` в Vault): агент готовит содержимое и коммит, но **каждый**
`git push` требует твоего отдельного подтверждения в чате.
