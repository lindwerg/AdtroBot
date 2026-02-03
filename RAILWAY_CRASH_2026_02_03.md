# Railway Crash - 2026-02-03

**Время:** 14:22 MSK  
**Длительность простоя:** ~9 минут (14:22 → 14:31 фикс запушен, 14:34 деплой SUCCESS)

---

## 🔴 ПРОБЛЕМА

Health check не отвечал, сервис упал после последнего деплоя.

**Статус deployment:**
- `5e56e681-c64b-4689-9302-430fe4ec576e` - **CRASHED** (14:22:15)
- 2 предыдущих деплоя - **FAILED**

**Ошибка в логах:**
```
ERROR [alembic.util.messaging] Multiple head revisions are present for given argument 'head'; 
please specify a specific target revision, '<branchname>@head' to narrow to a specific head, 
or 'heads' for all heads

FAILED: Multiple head revisions are present for given argument 'head'
```

---

## 🔍 ПРИЧИНА

**Конфликт миграций Alembic** - две "головных" ревизии:

1. `12302cba8088` (drop_image_assets_table) - старая ветка
2. `c9d0e1f2g3h4` (add_channel_promo_shown) - новая миграция из коммита `c0fb248`

Обе ответвлялись от `bb3aea586917` (add_ai_usage_table), но не были объединены.

**Почему произошло:**
- Была создана новая миграция `add_channel_promo_shown` без проверки истории миграций
- `alembic revision --autogenerate` создал новую миграцию, но не заметил что уже есть другая head-ревизия
- При деплое `alembic upgrade head` не смог определить какую из двух heads применять

---

## ✅ РЕШЕНИЕ

1. **Проверил историю миграций:**
   ```bash
   alembic branches -v
   alembic heads
   ```
   
2. **Создал merge-миграцию:**
   ```bash
   alembic merge -m "merge_heads" c9d0e1f2g3h4 12302cba8088
   ```
   
3. **Результат:** одна head-ревизия `195478ad60d2` которая объединяет обе ветки

4. **Закоммитил и запушил:**
   ```bash
   git add migrations/versions/2026_02_03_195478ad60d2_merge_heads.py
   git commit -m "Fix: Merge migration heads (195478ad60d2)"
   git push origin main
   ```

5. **Railway автоматически задеплоил** (деплой `4baf2836-6505-4604-96dd-4935a20b58e3`)

---

## ✅ ПРОВЕРКА ПОСЛЕ ПОЧИНКИ

**Health check (14:34):**
```json
{
  "status": "healthy",
  "checks": {
    "database": {"healthy": true, "latency_ms": 174.06},
    "scheduler": {"healthy": true, "message": "8 jobs scheduled"},
    "openrouter": {"healthy": true, "latency_ms": 277.23},
    "telegram": {"healthy": true, "message": "@Astraro_bot", "latency_ms": 9.29}
  }
}
```

**Статусы:**
- ✅ `/health` → 200 OK
- ✅ `/` → 200 OK (API running)
- ✅ `/admin/` → 200 OK (админка работает)
- ✅ `/docs` → 200 OK (Swagger UI работает)
- ✅ Telegram Bot API → `getMe` ok
- ✅ Webhook → установлен, 0 pending updates

---

## 📝 УРОКИ

### Что сломалось:
- Миграция Alembic с несколькими heads привела к краху при деплое
- Команда `alembic upgrade head` не смогла определить целевую ревизию

### Почему не заметил сразу:
- Не проверил историю миграций перед созданием новой (`alembic heads`)
- Не запустил `alembic upgrade head` локально перед пушем
- Railway не отправляет алерты о crash (нужно настроить мониторинг)

### Как избежать в будущем:

**1. ВСЕГДА проверять миграции перед созданием новой:**
```bash
# Перед alembic revision --autogenerate
alembic heads  # должна быть ОДНА head
alembic history --verbose  # проверить линейность
```

**2. ВСЕГДА тестировать миграции локально:**
```bash
# После создания миграции
alembic upgrade head  # применить локально
alembic downgrade -1  # откатить
alembic upgrade head  # применить снова
```

**3. ВСЕГДА проверять /health после деплоя:**
```bash
curl https://adtrobot-production.up.railway.app/health
```

**4. Настроить мониторинг:**
- Railway alerting на crash (Slack/Telegram webhook)
- UptimeRobot для /health endpoint (минута downtime → алерт)
- Prometheus alerts для метрик здоровья

**5. Pre-commit hook для миграций:**
Добавить в `.git/hooks/pre-push`:
```bash
#!/bin/bash
HEADS=$(alembic heads | wc -l)
if [ "$HEADS" -ne 1 ]; then
  echo "ERROR: Multiple migration heads detected! Merge them first."
  exit 1
fi
```

**6. CI/CD проверка:**
Добавить в GitHub Actions:
```yaml
- name: Check migrations
  run: |
    alembic heads
    test $(alembic heads | wc -l) -eq 1
```

---

## 📊 TIMELINE

- **14:22:08** - Пуш коммита `c0fb248` (Add @astraro_daily channel mention)
- **14:22:15** - Railway начал деплой `5e56e681` → CRASHED
- **14:30:00** - Начало диагностики (получение логов)
- **14:31:26** - Создана merge-миграция `195478ad60d2`
- **14:31:39** - Пуш фикса → Railway начал новый деплой `4baf2836`
- **14:32:xx** - Статус BUILDING
- **14:33:xx** - Статус DEPLOYING
- **14:34:xx** - Статус SUCCESS ✅
- **14:34:xx** - Проверка health checks - всё работает ✅

**Итого:** ~12 минут от крэша до восстановления.

---

## 🔧 РЕКОМЕНДАЦИИ

1. **Добавить pre-commit/pre-push hooks** для проверки миграций
2. **Настроить UptimeRobot** с алертами в Telegram
3. **Добавить Railway webhook** для нотификаций о deploy status
4. **Создать runbook** с чеклистом для деплоя:
   - ☑️ alembic heads проверен
   - ☑️ миграции применены локально
   - ☑️ тесты пройдены
   - ☑️ /health проверен после деплоя
5. **Автоматический rollback** если health check фейлится после деплоя (Railway deployment healthcheck)

---

**Статус:** ✅ ПОЧИНЕНО  
**Автор:** Joy (OpenClaw agent)  
**Дата:** 2026-02-03 14:35 MSK
