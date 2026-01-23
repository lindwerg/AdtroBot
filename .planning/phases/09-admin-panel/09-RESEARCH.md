# Phase 9: Admin Panel - Research

**Researched:** 2026-01-23
**Domain:** Web Admin Dashboard (FastAPI + React SPA)
**Confidence:** HIGH

## Summary

Admin Panel для Telegram бота - это классическая задача построения CRUD-интерфейса с аналитическим dashboard. Стек определен контекстом: FastAPI backend (уже есть), React SPA frontend с Ant Design для UI компонентов, Recharts для визуализации.

Основные технические решения:
1. **Backend**: FastAPI endpoints под `/admin/*` с JWT аутентификацией (python-jose + passlib[bcrypt])
2. **Frontend**: React + TypeScript + Vite, Ant Design ProComponents для таблиц/форм, Recharts для графиков
3. **Auth**: JWT токены (30 min expiry), username/password в отдельной Admin таблице
4. **Messaging**: aiogram Bot.send_message через существующий get_bot() + APScheduler для отложенных рассылок

**Primary recommendation:** Использовать Ant Design ProTable для user management (встроенные фильтры, сортировка, пагинация) + Recharts ComposedChart для dashboard метрик.

## Standard Stack

### Core (Backend)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115+ | API framework | Уже в проекте, native async |
| python-jose[cryptography] | 3.3.0 | JWT токены | Официальная рекомендация FastAPI |
| passlib[bcrypt] | 1.7.4 | Password hashing | Индустриальный стандарт, bcrypt |
| pandas | 2.2+ | Data export | CSV/Excel экспорт, aggregation |

### Core (Frontend)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 19.x | UI framework | Decision locked in CONTEXT |
| TypeScript | 5.7+ | Type safety | Modern SPA standard |
| Vite | 6.x | Build tool | Fast HMR, native ESM |
| Ant Design | 5.26+ | UI components | Enterprise admin components |
| @ant-design/pro-components | 2.8+ | Admin-specific | ProTable, ProForm out-of-box |
| Recharts | 2.15+ | Charts | React-native, declarative |
| React Router | 7.x | Routing | Protected routes, middleware |
| Axios | 1.7+ | HTTP client | Interceptors for JWT refresh |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| react-query (TanStack Query) | 5.x | Data fetching | Server state management |
| dayjs | 1.11+ | Date handling | Lightweight, Ant Design compatible |
| zustand | 5.x | State | Simple global state (user, auth) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Ant Design | MUI | MUI more design-flexible, Ant Design better admin components |
| Recharts | Chart.js | Chart.js more customizable, Recharts simpler React integration |
| python-jose | PyJWT | PyJWT simpler, python-jose has JWK/JWS support |
| pandas | raw SQL | pandas easier aggregation, SQL more performant for large data |

**Installation (Backend):**
```bash
pip install python-jose[cryptography] passlib[bcrypt] pandas openpyxl
# or in pyproject.toml:
# python-jose = {extras = ["cryptography"], version = "^3.3.0"}
# passlib = {extras = ["bcrypt"], version = "^1.7.4"}
# pandas = "^2.2.0"
# openpyxl = "^3.1.0"  # for Excel export
```

**Installation (Frontend):**
```bash
npm create vite@latest admin -- --template react-ts
cd admin
npm install antd @ant-design/pro-components @ant-design/icons recharts react-router axios @tanstack/react-query dayjs zustand
```

## Architecture Patterns

### Recommended Project Structure

```
src/
├── admin/                    # Admin backend module
│   ├── __init__.py
│   ├── router.py            # FastAPI router, all /admin/* endpoints
│   ├── auth.py              # JWT logic, password hashing
│   ├── schemas.py           # Pydantic models for admin API
│   ├── services/
│   │   ├── users.py         # User CRUD + search
│   │   ├── analytics.py     # Metrics queries
│   │   ├── messaging.py     # Send message to user
│   │   └── export.py        # CSV/Excel generation
│   └── models.py            # Admin user model
│
admin-frontend/              # Separate React app
├── src/
│   ├── api/                 # API client, interceptors
│   │   ├── client.ts
│   │   └── endpoints/
│   ├── components/
│   │   ├── charts/          # Dashboard charts
│   │   ├── tables/          # User tables
│   │   └── forms/           # Edit forms
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Users.tsx
│   │   ├── Subscriptions.tsx
│   │   ├── Payments.tsx
│   │   ├── Messages.tsx
│   │   └── Login.tsx
│   ├── hooks/               # React Query hooks
│   ├── store/               # Zustand stores
│   ├── routes/              # Route definitions
│   └── utils/
└── vite.config.ts
```

### Pattern 1: JWT Authentication Flow

**What:** OAuth2 password bearer с JWT токенами
**When to use:** Всегда для admin API
**Example:**
```python
# Source: FastAPI official docs + python-jose
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = "your-secret-key-from-env"  # openssl rand -hex 32
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/token")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_admin(token: str = Depends(oauth2_scheme)) -> Admin:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    # Get admin from DB...
    return admin
```

### Pattern 2: CORS Configuration for SPA

**What:** Разрешить запросы от frontend dev server
**When to use:** Development и production
**Example:**
```python
# Source: FastAPI CORS docs
from fastapi.middleware.cors import CORSMiddleware

# In main.py after app = FastAPI()
origins = [
    "http://localhost:5173",      # Vite dev server
    "http://localhost:3000",      # Alternative dev port
    "https://admin.yourdomain.com",  # Production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Pattern 3: ProTable with Server-Side Data

**What:** Ant Design ProTable с backend pagination/filter/sort
**When to use:** User list, payments, subscriptions tables
**Example:**
```tsx
// Source: Ant Design ProComponents docs
import { ProTable, ProColumns } from '@ant-design/pro-components';
import { api } from '@/api/client';

interface User {
  id: number;
  telegram_id: number;
  username: string | null;
  zodiac_sign: string | null;
  is_premium: boolean;
  created_at: string;
}

const columns: ProColumns<User>[] = [
  { dataIndex: 'telegram_id', title: 'Telegram ID', copyable: true },
  { dataIndex: 'username', title: 'Username' },
  {
    dataIndex: 'zodiac_sign',
    title: 'Знак',
    valueType: 'select',
    valueEnum: {
      aries: { text: 'Овен' },
      taurus: { text: 'Телец' },
      // ... all 12 signs
    },
  },
  {
    dataIndex: 'is_premium',
    title: 'Статус',
    valueType: 'select',
    valueEnum: {
      true: { text: 'Premium', status: 'Success' },
      false: { text: 'Free', status: 'Default' },
    },
  },
  { dataIndex: 'created_at', title: 'Регистрация', valueType: 'dateTime' },
];

export default function UsersPage() {
  return (
    <ProTable<User>
      columns={columns}
      request={async (params, sort, filter) => {
        const { data } = await api.get('/admin/users', {
          params: { ...params, ...sort, ...filter },
        });
        return { data: data.items, total: data.total, success: true };
      }}
      rowKey="id"
      pagination={{ pageSize: 20 }}
      search={{ filterType: 'light' }}
      rowSelection={{}}
      toolBarRender={() => [
        <Button key="export">Экспорт CSV</Button>,
      ]}
    />
  );
}
```

### Pattern 4: Dashboard KPI Card with Sparkline

**What:** KPI карточка с hero value + trend + micro-chart
**When to use:** Dashboard metrics display
**Example:**
```tsx
// Source: Recharts + custom component
import { Card, Statistic } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { AreaChart, Area, ResponsiveContainer } from 'recharts';

interface KPICardProps {
  title: string;
  value: number | string;
  trend: number;  // percentage change, positive = good
  sparklineData: { value: number }[];
  prefix?: string;
  invertTrend?: boolean;  // true for metrics where decrease is good (errors)
}

export function KPICard({ title, value, trend, sparklineData, prefix, invertTrend }: KPICardProps) {
  const isPositive = invertTrend ? trend < 0 : trend > 0;
  const trendColor = isPositive ? '#3f8600' : '#cf1322';

  return (
    <Card size="small">
      <Statistic
        title={title}
        value={value}
        prefix={prefix}
        suffix={
          <span style={{ color: trendColor, fontSize: 14 }}>
            {isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
            {Math.abs(trend)}%
          </span>
        }
      />
      <ResponsiveContainer width="100%" height={40}>
        <AreaChart data={sparklineData}>
          <Area
            type="monotone"
            dataKey="value"
            stroke={trendColor}
            fill={trendColor}
            fillOpacity={0.1}
          />
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  );
}
```

### Pattern 5: Funnel Visualization

**What:** Воронка продаж с drop-off показателями
**When to use:** Conversion funnel display
**Example:**
```tsx
// Source: Custom component (Recharts doesn't have native funnel)
import { FunnelChart, Funnel, LabelList, Tooltip, ResponsiveContainer } from 'recharts';

interface FunnelStage {
  name: string;
  value: number;
  fill: string;
}

// Using Recharts FunnelChart (available in v2.15+)
// Or custom horizontal bar visualization:
export function ConversionFunnel({ stages }: { stages: FunnelStage[] }) {
  const maxValue = stages[0]?.value || 1;

  return (
    <div>
      {stages.map((stage, idx) => {
        const prevValue = idx > 0 ? stages[idx - 1].value : stage.value;
        const dropoff = prevValue - stage.value;
        const dropoffPct = prevValue > 0 ? ((dropoff / prevValue) * 100).toFixed(1) : 0;
        const conversion = prevValue > 0 ? ((stage.value / prevValue) * 100).toFixed(1) : 100;

        return (
          <div key={stage.name} style={{ marginBottom: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div
                style={{
                  width: `${(stage.value / maxValue) * 100}%`,
                  minWidth: 20,
                  height: 32,
                  background: stage.fill,
                  borderRadius: 4,
                }}
              />
              <span>{stage.name}</span>
              <span style={{ fontWeight: 'bold' }}>{stage.value.toLocaleString()}</span>
              {idx > 0 && (
                <span style={{ color: '#52c41a' }}>{conversion}%</span>
              )}
            </div>
            {idx > 0 && dropoff > 0 && (
              <div style={{ fontSize: 12, color: '#ff4d4f', marginLeft: 8 }}>
                ↓ -{dropoffPct}% ({dropoff.toLocaleString()} users)
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
```

### Pattern 6: Send Message via Bot

**What:** Отправка сообщения пользователю через aiogram
**When to use:** Admin messaging feature
**Example:**
```python
# Source: aiogram docs + existing bot.py pattern
from src.bot.bot import get_bot

async def send_message_to_user(telegram_id: int, text: str) -> bool:
    """Send message to user via Telegram bot."""
    try:
        bot = get_bot()
        await bot.send_message(chat_id=telegram_id, text=text)
        return True
    except Exception as e:
        # User may have blocked bot, chat not found, etc.
        logger.warning(f"Failed to send message to {telegram_id}: {e}")
        return False

async def broadcast_message(
    session: AsyncSession,
    text: str,
    filters: dict,  # zodiac_sign, is_premium, etc.
) -> dict:
    """Send message to filtered users. Returns stats."""
    # Build query with filters
    query = select(User.telegram_id)
    if filters.get("is_premium") is not None:
        query = query.where(User.is_premium == filters["is_premium"])
    if filters.get("zodiac_sign"):
        query = query.where(User.zodiac_sign == filters["zodiac_sign"])
    # ... more filters

    result = await session.execute(query)
    telegram_ids = [row[0] for row in result.fetchall()]

    sent = 0
    failed = 0
    for tid in telegram_ids:
        if await send_message_to_user(tid, text):
            sent += 1
        else:
            failed += 1

    return {"sent": sent, "failed": failed, "total": len(telegram_ids)}
```

### Pattern 7: CSV Export Endpoint

**What:** Экспорт данных в CSV через StreamingResponse
**When to use:** Data export feature
**Example:**
```python
# Source: FastAPI StreamingResponse + pandas
import io
import pandas as pd
from fastapi.responses import StreamingResponse

@router.get("/admin/export/users")
async def export_users(
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
    zodiac_sign: str | None = None,
    is_premium: bool | None = None,
):
    """Export users to CSV."""
    query = select(User)
    if zodiac_sign:
        query = query.where(User.zodiac_sign == zodiac_sign)
    if is_premium is not None:
        query = query.where(User.is_premium == is_premium)

    result = await session.execute(query)
    users = result.scalars().all()

    # Convert to DataFrame
    data = [{
        "telegram_id": u.telegram_id,
        "username": u.username,
        "zodiac_sign": u.zodiac_sign,
        "is_premium": u.is_premium,
        "premium_until": u.premium_until,
        "created_at": u.created_at,
    } for u in users]

    df = pd.DataFrame(data)

    # Generate CSV
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)

    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"},
    )
```

### Anti-Patterns to Avoid

- **Storing JWT in localStorage:** Vulnerable to XSS. Use httpOnly cookies or memory-only storage with refresh tokens.
- **Blocking main loop with broadcast:** Use background tasks (APScheduler job) for large broadcasts.
- **N+1 queries in analytics:** Use SQLAlchemy aggregations and batch queries.
- **Hardcoded admin credentials:** Store hashed password in DB, allow password reset.
- **No rate limiting on login:** Add rate limiting to prevent brute force.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Password hashing | Custom hash | passlib CryptContext | Timing attacks, salt handling, algorithm upgrades |
| JWT validation | Manual parsing | python-jose | Signature verification, expiry, claims validation |
| Data tables | Custom table | ProTable | Sorting, filtering, pagination, selection built-in |
| Chart rendering | Canvas/SVG | Recharts | Responsive, tooltips, legends, animations |
| Date formatting | Manual | dayjs | Timezone, locale, relative time |
| Form validation | Manual | ProForm + Ant Design | Field validation, error display, async submit |

**Key insight:** Admin panels are a solved problem. Ant Design ProComponents exists specifically for this use case with years of enterprise refinement.

## Common Pitfalls

### Pitfall 1: Broadcast Blocking the Event Loop

**What goes wrong:** Sending messages to 10,000+ users blocks the server
**Why it happens:** Synchronous iteration, waiting for each message
**How to avoid:**
- Use APScheduler job for large broadcasts
- Implement batch processing with rate limiting (30 msg/sec Telegram limit)
- Return job ID immediately, poll for status
**Warning signs:** Request timeout, 502 errors during broadcast

### Pitfall 2: JWT Token Refresh Race Condition

**What goes wrong:** Multiple parallel requests get 401, all try to refresh
**Why it happens:** Token expires while multiple requests in flight
**How to avoid:**
- Implement token refresh queue in frontend
- Use axios interceptor with Promise queue
- Return new token in response header on each request
**Warning signs:** Random 401 errors, users getting logged out

### Pitfall 3: Pagination Offset Performance

**What goes wrong:** Page 1000 takes 10+ seconds
**Why it happens:** OFFSET N scans N rows before returning
**How to avoid:**
- Use cursor-based pagination (WHERE id > last_id)
- Limit max page number in UI
- For analytics, pre-aggregate data
**Warning signs:** Slow response times on later pages

### Pitfall 4: Frontend Build Size

**What goes wrong:** Initial load 2MB+, slow mobile experience
**Why it happens:** Importing entire Ant Design, all icons
**How to avoid:**
- Use tree-shaking imports: `import { Button } from 'antd'`
- Import icons individually: `import { UserOutlined } from '@ant-design/icons'`
- Code split routes with React.lazy()
**Warning signs:** Large bundle warnings from Vite

### Pitfall 5: CORS Credentials with Wildcards

**What goes wrong:** CORS error despite allow_origins=["*"]
**Why it happens:** Cannot use wildcard with allow_credentials=True
**How to avoid:** Explicitly list allowed origins when using credentials
**Warning signs:** CORS errors in console only when sending cookies

## Code Examples

### Complete Login Flow

```python
# Backend: /admin/token endpoint
# Source: FastAPI security tutorial
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.engine import get_session
from src.admin.auth import verify_password, create_access_token
from src.admin.models import Admin

router = APIRouter(prefix="/admin", tags=["admin"])

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    # Find admin by username
    result = await session.execute(
        select(Admin).where(Admin.username == form_data.username)
    )
    admin = result.scalar_one_or_none()

    if not admin or not verify_password(form_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": admin.username},
        expires_delta=timedelta(minutes=30),
    )
    return Token(access_token=access_token)
```

```tsx
// Frontend: Login page
// Source: Ant Design ProForm + React Router
import { LoginForm, ProFormText } from '@ant-design/pro-components';
import { LockOutlined, UserOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router';
import { api } from '@/api/client';
import { useAuthStore } from '@/store/auth';

export default function LoginPage() {
  const navigate = useNavigate();
  const setToken = useAuthStore((s) => s.setToken);

  return (
    <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 100 }}>
      <LoginForm
        title="Admin Panel"
        subTitle="AdtroBot"
        onFinish={async (values) => {
          const formData = new URLSearchParams();
          formData.append('username', values.username);
          formData.append('password', values.password);

          const { data } = await api.post('/admin/token', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          });

          setToken(data.access_token);
          navigate('/');
          return true;
        }}
      >
        <ProFormText
          name="username"
          fieldProps={{ size: 'large', prefix: <UserOutlined /> }}
          placeholder="Username"
          rules={[{ required: true }]}
        />
        <ProFormText.Password
          name="password"
          fieldProps={{ size: 'large', prefix: <LockOutlined /> }}
          placeholder="Password"
          rules={[{ required: true }]}
        />
      </LoginForm>
    </div>
  );
}
```

### Analytics Query Pattern

```python
# Backend: Analytics aggregation
# Source: SQLAlchemy aggregation patterns
from sqlalchemy import func, case, extract
from datetime import datetime, timedelta, timezone

async def get_dashboard_metrics(session: AsyncSession) -> dict:
    """Get all dashboard KPI metrics."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Total users
    total_users = await session.scalar(select(func.count(User.id)))

    # New users today
    new_today = await session.scalar(
        select(func.count(User.id))
        .where(User.created_at >= today_start)
    )
    new_yesterday = await session.scalar(
        select(func.count(User.id))
        .where(User.created_at >= yesterday_start)
        .where(User.created_at < today_start)
    )

    # Premium users
    premium_count = await session.scalar(
        select(func.count(User.id))
        .where(User.is_premium == True)
    )

    # Conversion rate (users who paid / total users with 7+ days)
    eligible_users = await session.scalar(
        select(func.count(User.id))
        .where(User.created_at <= week_ago)
    )
    paid_users = await session.scalar(
        select(func.count(func.distinct(Payment.user_id)))
        .where(Payment.status == "succeeded")
    )
    conversion_rate = (paid_users / eligible_users * 100) if eligible_users > 0 else 0

    # Revenue today
    revenue_today = await session.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.paid_at >= today_start)
        .where(Payment.status == "succeeded")
    ) or 0

    revenue_yesterday = await session.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.paid_at >= yesterday_start)
        .where(Payment.paid_at < today_start)
        .where(Payment.status == "succeeded")
    ) or 0

    return {
        "total_users": total_users,
        "new_users_today": new_today,
        "new_users_trend": calc_trend(new_today, new_yesterday),
        "premium_users": premium_count,
        "conversion_rate": round(conversion_rate, 2),
        "revenue_today_kopeks": revenue_today,
        "revenue_trend": calc_trend(revenue_today, revenue_yesterday),
    }

def calc_trend(current: int, previous: int) -> float:
    """Calculate percentage change."""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round((current - previous) / previous * 100, 1)
```

### Protected Route in React Router 7

```tsx
// Source: React Router 7 docs
import { createBrowserRouter, redirect } from 'react-router';

// Auth check loader
async function requireAuth() {
  const token = localStorage.getItem('token');
  if (!token) {
    throw redirect('/login');
  }
  // Optionally validate token with backend
  return null;
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    loader: requireAuth,
    element: <Layout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'users', element: <UsersPage /> },
      { path: 'users/:id', element: <UserDetailPage /> },
      { path: 'subscriptions', element: <SubscriptionsPage /> },
      { path: 'payments', element: <PaymentsPage /> },
      { path: 'messages', element: <MessagesPage /> },
      { path: 'promo-codes', element: <PromoCodesPage /> },
      { path: 'ab-tests', element: <ABTestsPage /> },
    ],
  },
]);
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Create React App | Vite | 2023 | 10x faster builds, native ESM |
| Class components | Hooks + functional | 2019 | Simpler code, better composition |
| Redux for everything | React Query + Zustand | 2021 | Less boilerplate, better caching |
| Moment.js | dayjs | 2020 | 97% smaller bundle |
| REST pagination offset | Cursor-based | Standard | Better performance at scale |
| Ant Design v4 | Ant Design v5 | 2023 | CSS-in-JS, design tokens |

**Deprecated/outdated:**
- **Create React App (CRA):** Officially deprecated, use Vite
- **Moment.js:** Use dayjs or date-fns
- **Class components:** Use functional with hooks
- **Redux Toolkit for simple state:** Overkill, use Zustand

## Open Questions

1. **Scheduled Messages Storage**
   - What we know: APScheduler can schedule jobs, needs job store
   - What's unclear: Best way to store scheduled message content
   - Recommendation: Create ScheduledMessage model, APScheduler stores job_id reference

2. **A/B Test Implementation**
   - What we know: Need to assign users to variants, track metrics
   - What's unclear: Exact variant assignment algorithm
   - Recommendation: Hash(user_id + experiment_id) % 100 for consistent assignment

3. **UTM Tracking**
   - What we know: Telegram start parameter can contain utm data
   - What's unclear: Exact format of start parameter parsing
   - Recommendation: Use `start=utm_source_medium_campaign` format, parse on /start

## Sources

### Primary (HIGH confidence)
- `/websites/fastapi_tiangolo` - JWT auth, CORS, OAuth2PasswordBearer
- `/recharts/recharts` - Chart components, ResponsiveContainer
- `/ant-design/ant-design` - Table, Pagination, ProTable patterns
- `/mpdavis/python-jose` - JWT encode/decode examples
- `/websites/passlib_readthedocs_io_en_stable` - bcrypt hashing patterns
- `/remix-run/react-router` - Protected routes, auth middleware
- `/vitejs/vite` - React TypeScript setup, backend integration

### Secondary (MEDIUM confidence)
- [FastAPI JWT Auth Guide - TestDriven.io](https://testdriven.io/blog/fastapi-jwt-auth/)
- [Ant Design ProComponents](https://procomponents.ant.design/en-US/)
- [MUI X Funnel Charts](https://mui.com/x/react-charts/funnel/)
- [FastAPI CSV Export - Medium](https://medium.com/@liamwr17/supercharge-your-apis-with-csv-and-excel-exports-fastapi-pandas-a371b2c8f030)
- [APScheduler with FastAPI - Medium](https://rajansahu713.medium.com/implementing-background-job-scheduling-in-fastapi-with-apscheduler-6f5fdabf3186)

### Tertiary (LOW confidence)
- Web search results for admin panel best practices - requires validation against official docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Verified with Context7 and official docs
- Architecture: HIGH - Based on FastAPI and React best practices
- Pitfalls: MEDIUM - Mix of documented issues and community experience

**Research date:** 2026-01-23
**Valid until:** 2026-02-23 (30 days - stable technologies)
