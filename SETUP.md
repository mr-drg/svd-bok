# Настройка публикации на GitHub Pages

Разовая настройка уже выполнена: аккаунт `mr-drg`, репозиторий
`mr-drg/svd-bok` (переименован из `quatz-site`), SSH-ключ, GitHub Pages
(Source: GitHub Actions). Сайт: https://mr-drg.github.io/svd-bok/

Этот файл — памятка на случай переустановки с нуля на новой машине.

## 1. Аккаунт GitHub

Если аккаунта ещё нет — зарегистрируйся на https://github.com (бесплатный
план полностью достаточен). Агент не создаёт аккаунты и не работает с
паролями/токенами в чате — это делает пользователь сам.

## 2. Создать пустой репозиторий

На https://github.com/new:
- Repository name: `svd-bok` (или другое — тогда поправь `baseUrl` в
  `quartz.config.yaml` и `git remote` ниже).
- Public.
- **Не** добавлять README/gitignore/license — репозиторий уже наполнен
  локально, просто подключаешь существующую папку.

## 3. Настроить git-аутентификацию на этой машине

- **SSH-ключ**: `ssh-keygen -t ed25519 -C "твой-email"`, затем добавить
  публичный ключ (`~/.ssh/id_ed25519.pub`) в
  https://github.com/settings/keys.
- Агент не должен видеть и не запрашивает сам токен/пароль.

## 4. Подключить локальный репозиторий

```bash
cd ~/Sites/svd-bok
git remote add origin git@github.com:<твой-логин>/svd-bok.git
git push -u origin main
```

## 5. Включить GitHub Pages

Settings → Pages → Source → **GitHub Actions**. Workflow
`.github/workflows/deploy.yml` уже в репозитории — собирает сайт
(`npx quartz build`) и деплоит на Pages при каждом push в `main`.

## 6. `baseUrl` и заголовок

В `quartz.config.yaml`:
```yaml
baseUrl: <твой-логин>.github.io/<имя-репозитория>
pageTitle: "<заголовок сайта>"
```

## Если переименовываешь репозиторий на GitHub

Rename на GitHub меняет URL Pages сразу — но собранный сайт хранит старый
`baseUrl` во внутренних ссылках/og-превью/данных графа связей, из-за чего
граф и ассеты перестают резолвиться, пока не обновишь на своей стороне:

```bash
mv ~/Sites/<старое-имя> ~/Sites/<новое-имя>
cd ~/Sites/<новое-имя>
git remote set-url origin git@github.com:<логин>/<новое-имя>.git
```

+ поправить `baseUrl` в `quartz.config.yaml`, пересобрать, запушить.

## Дальше

Публикация — через ежедневный ритуал (скилл `quatz-publish` в Vault):
агент готовит содержимое и коммит, но **каждый** `git push` требует
отдельного подтверждения в чате.
