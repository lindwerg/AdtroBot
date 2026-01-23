# Phase 9: Admin Panel - Context

**Gathered:** 2026-01-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Веб-интерфейс (admin panel) для управления ботом и анализа метрик. Админка — это отдельное SPA приложение с dashboard'ом, управлением пользователями, messaging системой и аналитикой. Не включает изменения в самом боте или платежной системе.

</domain>

<decisions>
## Implementation Decisions

### Dashboard UI и метрики

**KPI карточки (главный экран):**
1. **Growth & Activity:**
   - Active Users (DAU / MAU)
   - New Users (сегодня/неделя + % прирост)
   - Retention Rate (D1, D7, D30 cohort)

2. **Product Metrics:**
   - Total Horoscopes Delivered (за сегодня)
   - Tarot Spreads Completed (завершенные циклы)
   - Popular Services Breakdown (мини-рейтинг топ услуг)

3. **Revenue:**
   - Total Revenue (сегодня/месяц + прогресс-бар плана)
   - Conversion Rate (% free→paid)
   - ARPU (средний чек на пользователя)

4. **Bot Health:**
   - Error Rate / Fallback Rate (% ошибок)
   - Avg. Response Time (ms)

5. **API Costs:**
   - Затраты на OpenRouter (сегодня/месяц)

6. **Insight Card:**
   - Most Active Zodiac Sign (самый активный знак сегодня)

**Trend visualization:**
- Каждая KPI карточка включает:
  - Hero Value (крупная цифра)
  - Trend Indicator: стрелка ↑/↓ + процент изменения + цветовой код (зеленый/красный)
  - Micro-chart (sparkline) внизу карточки

**Цветовое кодирование:**
- Зеленый: рост выручки, пользователей, завершенных раскладов
- Красный: рост ошибок, отписок, падение выручки
- Нейтральный (серый/синий): объемные метрики без "хорошо/плохо"

**Период сравнения:**
- Для оперативных метрик (revenue, DAU): vs Yesterday
- Для итоговых (MAU, Retention): vs Last 30 Days или MoM

**Фильтры:**
- Быстрые пресеты: 24h, 7d, 30d, All time (кнопки наверху)
- Без custom date range picker (только пресеты)

### Воронка и конверсия

**Визуализация:**
- Комбинированный виджет: слева полоски (ширина = объем), справа цифры
- Структура каждого этапа:
  - Полоска (ширина показывает объем)
  - Цифры: количество + % конверсии в badge
  - Drop-off стрелка ↓ с процентом и числом потерь

**Этапы воронки (детальные):**
1. Регистрация (/start)
2. Onboarding завершен (ввел дату, получил первый прогноз)
3. Первое использование (гороскоп/таро/натальная карта)
4. Увидел premium teaser (лимит или premium кнопка)
5. Нажал "Подписка" (перешел на страницу планов)
6. Выбрал план (299₽ или 699₽)
7. Перешел на ЮКасса (clicked payment URL)
8. Оплатил (payment succeeded)

**Показывать ВСЕ действия пользователя** — максимально детально для понимания где drop-off.

**Drop-off отображение:**
- Процент + количество: "-40% (4,960 users)"

### Управление пользователями

**Список пользователей (полный):**
- Таблица с колонками:
  - Telegram ID
  - Username (@username или "—")
  - Имя (first_name из Telegram или введенное)
  - Дата регистрации (created_at)
  - Знак зодиака
  - Статус (Free/Premium)
  - Premium до (premium_until)
  - Пол (gender) — если собираем
  - Последняя активность

**Поиск и фильтры:**
- По Telegram ID
- По username
- По знаку зодиака (dropdown 12 знаков)
- По статусу (Free/Premium)
- По дате регистрации (диапазон дат)
- По полу
- По количеству оставшихся прогнозов
- По purchase (купил детальную натальную карту или нет)

**Действия для конкретного юзера:**
1. Просмотр профиля (все данные, история, платежи)
2. Управление подпиской:
   - Активировать premium
   - Отменить подписку
   - Продлить подписку
   - Изменить план
3. Отправить сообщение (DM)
4. Блокировка/бан
5. Выдать дополнительные кредиты (бонусные прогнозы)
6. Подарки:
   - Подарить месяц premium
   - Подарить доступ к детальной натальной карте
   - Подарить X таро раскладов

**Массовые операции (bulk actions):**
- Чекбоксы для выбора нескольких юзеров
- Bulk send message
- Bulk activate/cancel subscriptions
- Bulk ban/unban
- Bulk gift credits

### Messaging система

**Типы отправки:**
1. Одному юзеру (DM из профиля)
2. Группе (сегмент по фильтрам)
3. Всем юзерам (broadcast)

**Шаблоны:**
- Нет (пишу текст каждый раз вручную)

**Сегменты для групповой рассылки:**
- По статусу (free/premium)
- По знаку зодиака
- По активности (активные за последние 7d/30d)
- По дате регистрации (новые/старые)
- По полу
- По количеству оставшихся прогнозов
- По purchase detailed natal (купил или нет)

**Scheduling:**
- Да, с выбором даты/времени (отложенная отправка)

**История сообщений:**
- Да, с статистикой:
  - Кто получил
  - Delivered count
  - Read rate (если Telegram API позволяет)

### Дополнительный функционал

**Экспорт данных:**
- CSV/Excel экспорт:
  - Список пользователей (с фильтрами)
  - Платежи
  - Метрики за период

**Промокоды:**
- Создание promo codes
- Настройка:
  - Код (текст)
  - Скидка (% или фиксированная сумма)
  - Срок действия
  - Количество использований (лимит)
  - Условия (для новых/для всех)
- Просмотр статистики использования

**UTM метки (tracking источников):**
- Создание UTM-меток (utm_source, utm_medium, utm_campaign)
- Уникальные ссылки для отслеживания (t.me/adtrobot?start=utm_xxx)
- Dashboard показывает:
  - Источник → количество регистраций
  - Источник → конверсия в premium
  - Источник → LTV (lifetime value)

**A/B тесты:**
- Управление экспериментами:
  - Название теста
  - Варианты (A/B/C)
  - Метрика успеха (conversion, retention, revenue)
  - Распределение трафика (50/50, 80/20)
  - Старт/стоп
- Результаты:
  - Статистика по вариантам
  - Победитель (statistical significance)

### Tech Stack

**Backend:**
- FastAPI (уже используется в проекте)
- SQLAlchemy async (existing DB)
- Endpoints: `/admin/*`

**Frontend:**
- React SPA (или Vue — Claude's choice на основе экосистемы)
- Mobile-first, полностью responsive (использование с телефона)

**UI Framework:**
- Claude's Discretion (Material UI, Ant Design, or Chakra UI)
- Выбрать на основе:
  - Best dashboard/admin components
  - Mobile responsiveness
  - Chart library support

**Auth:**
- Username + Password
- Хранить в DB: Admin model (username, hashed_password)
- JWT токены для session

**Charts:**
- Recharts или Chart.js (Claude's choice)
- Sparklines для KPI cards
- Funnel visualization
- Line/bar charts для метрик

### Claude's Discretion

- Выбор между React и Vue (на основе экосистемы и компонентов)
- Выбор UI framework (MUI/Ant Design/Chakra)
- Выбор chart library
- Exact layout и spacing
- Color palette (кроме семантических цветов для trends)
- API endpoint naming conventions
- Pagination strategies
- Loading states и skeletons
- Error handling UI

</decisions>

<specifics>
## Specific Ideas

- "Должен работать с телефона" — mobile-first critical
- "Видеть прям все что может пользователь сделать" — детальная воронка с каждым action
- "Максимально полное по лучшим практикам" — industry-standard admin panel features
- "Чтобы больше к этому не возвращаться" — complete feature set, extensible

**Visual References:**
- KPI cards: Hero value + trend indicator + sparkline (стандарт для SaaS dashboards)
- Funnel: Combined visualization (bars + numbers + drop-off arrows)

</specifics>

<deferred>
## Deferred Ideas

Нет — обсуждение осталось в рамках Phase 9 (Admin Panel).

Performance improvements (фоновая генерация гороскопов, кэширование) — это todos для следующего milestone, не часть Admin Panel.

</deferred>

---

*Phase: 09-admin-panel*
*Context gathered: 2026-01-23*
