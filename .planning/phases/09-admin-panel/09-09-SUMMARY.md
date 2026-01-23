---
phase: 09
plan: 09
subsystem: admin-panel
tags: [promo-codes, crud, admin-ui, react, fastapi]

dependency-graph:
  requires: ["09-01"]
  provides: ["promo-code-management", "promo-crud-api", "promo-ui"]
  affects: ["09-10", "payment-processing"]

tech-stack:
  added: []
  patterns:
    - ProTable with server-side request
    - ModalForm for promo creation
    - Switch for active toggle
    - Popconfirm for delete confirmation
    - Progress bar for usage visualization

key-files:
  created:
    - src/admin/services/promo.py
    - admin-frontend/src/api/endpoints/promo.ts
    - admin-frontend/src/pages/PromoCodes.tsx
  modified:
    - src/admin/schemas.py
    - src/admin/router.py
    - admin-frontend/src/routes/index.tsx

decisions:
  - key: promo-code-uppercase
    choice: Auto uppercase codes on creation
    reason: Consistency and easier matching

metrics:
  duration: 5 min
  completed: 2026-01-23
---

# Phase 9 Plan 9: Promo Codes Management Summary

**TL;DR:** Полный CRUD для промокодов с API и UI - создание, просмотр, активация/деактивация, удаление.

## What Was Built

### Backend (src/admin/services/promo.py)

**Promo code schemas:**
- `CreatePromoCodeRequest`: code, discount_percent, valid_until, max_uses, partner fields
- `PromoCodeListItem`: full promo data with usage stats
- `PromoCodeListResponse`: paginated list
- `UpdatePromoCodeRequest`: partial update support

**Promo code service:**
- `create_promo_code()`: создание с uppercase нормализацией и проверкой дубликатов
- `list_promo_codes()`: пагинированный список с фильтром по активности
- `update_promo_code()`: частичное обновление любых полей
- `delete_promo_code()`: удаление по id

**API endpoints:**
- `POST /admin/promo-codes` → создание промокода
- `GET /admin/promo-codes` → список с пагинацией и фильтром is_active
- `PATCH /admin/promo-codes/{id}` → обновление
- `DELETE /admin/promo-codes/{id}` → удаление

### Frontend (admin-frontend/src/pages/PromoCodes.tsx)

**API client (promo.ts):**
- TypeScript интерфейсы для всех типов
- Функции для всех CRUD операций

**PromoCodes page:**
- ProTable с серверной пагинацией
- Колонки: код (Tag), скидка, использований (Progress), срок, статус (Switch), дата
- Фильтр по активности (valueEnum)
- Create modal с ModalForm
- Delete с Popconfirm
- React Query mutations с cache invalidation

## Commits

| Hash | Description |
|------|-------------|
| 5eacfd7 | Promo code schemas and service |
| 4c06790 | Promo code API endpoints |
| c3a388a | Frontend promo codes management page |

## Deviations from Plan

None - план выполнен точно как написано.

## Key Files

```
src/admin/services/promo.py         # CRUD service
src/admin/schemas.py                # Pydantic schemas (added)
src/admin/router.py                 # API endpoints (added)
admin-frontend/src/api/endpoints/promo.ts    # API client
admin-frontend/src/pages/PromoCodes.tsx      # Management page
admin-frontend/src/routes/index.tsx          # Route registration
```

## Testing Verification

- [x] TypeScript компилируется без ошибок
- [x] Python синтаксис валиден
- [x] Импорты работают корректно
- [x] Все endpoints добавлены

## Next Phase Readiness

**Готово для:**
- 09-10: Analytics and reports (independent)
- Использование промокодов при оплате (когда будет реализовано в payment flow)

**Нет блокеров.**
