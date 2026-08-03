# quatz-site

Личный сайт-digital garden на [Quartz](https://quartz.jzhao.xyz), питается
куратированным подмножеством заметок из личной базы знаний (Vault_skynet,
`20_Cards/20.7_Publish/`).

Контент попадает сюда только через `scripts/sync_from_vault.py` и только
после ежедневной модерации в чате (см. скилл `quatz-publish` в Vault) —
не редактируй `content/` напрямую, изменения потеряются при следующей
синхронизации.

Первичная настройка (аккаунт GitHub, репозиторий, Pages, git-аутентификация)
описана в [SETUP.md](./SETUP.md).

## Локальная сборка/просмотр

```bash
npm install
npx quartz build --serve
```

Построено на [Quartz](https://github.com/jackyzha0/quartz) (MIT).
