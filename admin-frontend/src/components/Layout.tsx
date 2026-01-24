import { ProLayout, PageContainer } from '@ant-design/pro-components'
import {
  DashboardOutlined,
  UserOutlined,
  CreditCardOutlined,
  MessageOutlined,
  GiftOutlined,
  ExperimentOutlined,
  LogoutOutlined,
  StarOutlined,
  FileTextOutlined,
  MonitorOutlined,
} from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router'
import { useAuthStore } from '@/store/auth'

const menuItems = [
  { path: '/', name: 'Dashboard', icon: <DashboardOutlined /> },
  { path: '/users', name: 'Пользователи', icon: <UserOutlined /> },
  { path: '/subscriptions', name: 'Подписки', icon: <CreditCardOutlined /> },
  { path: '/payments', name: 'Платежи', icon: <CreditCardOutlined /> },
  { path: '/tarot-spreads', name: 'Расклады', icon: <StarOutlined /> },
  { path: '/messages', name: 'Сообщения', icon: <MessageOutlined /> },
  { path: '/content', name: 'Контент', icon: <FileTextOutlined /> },
  { path: '/promo-codes', name: 'Промокоды', icon: <GiftOutlined /> },
  { path: '/ab-tests', name: 'A/B тесты', icon: <ExperimentOutlined /> },
  { path: '/monitoring', name: 'Мониторинг', icon: <MonitorOutlined /> },
]

export default function Layout() {
  const navigate = useNavigate()
  const location = useLocation()
  const logout = useAuthStore((s) => s.logout)

  return (
    <ProLayout
      title="AdtroBot"
      logo={false}
      location={{ pathname: location.pathname }}
      route={{
        path: '/',
        routes: menuItems.map((item) => ({
          path: item.path,
          name: item.name,
          icon: item.icon,
        })),
      }}
      menuItemRender={(item, dom) => (
        <div onClick={() => navigate(item.path || '/')}>{dom}</div>
      )}
      avatarProps={{
        icon: <UserOutlined />,
        title: 'Admin',
        render: (_, dom) => dom,
      }}
      actionsRender={() => [
        <LogoutOutlined
          key="logout"
          onClick={() => {
            logout()
            navigate('/login')
          }}
          style={{ cursor: 'pointer' }}
        />,
      ]}
      fixedHeader
      fixSiderbar
    >
      <PageContainer>
        <Outlet />
      </PageContainer>
    </ProLayout>
  )
}
