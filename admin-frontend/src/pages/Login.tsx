import { LoginForm, ProFormText } from '@ant-design/pro-components'
import { LockOutlined, UserOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router'
import { message } from 'antd'
import { api } from '@/api/client'
import { useAuthStore } from '@/store/auth'

export default function LoginPage() {
  const navigate = useNavigate()
  const setToken = useAuthStore((s) => s.setToken)

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: '#f0f2f5',
    }}>
      <LoginForm
        title="AdtroBot Admin"
        subTitle="Панель администратора"
        onFinish={async (values) => {
          try {
            const formData = new URLSearchParams()
            formData.append('username', values.username)
            formData.append('password', values.password)

            const { data } = await api.post('/token', formData, {
              headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            })

            setToken(data.access_token)
            message.success('Вход выполнен')
            navigate('/')
            return true
          } catch {
            message.error('Неверный логин или пароль')
            return false
          }
        }}
      >
        <ProFormText
          name="username"
          fieldProps={{ size: 'large', prefix: <UserOutlined /> }}
          placeholder="Логин"
          rules={[{ required: true, message: 'Введите логин' }]}
        />
        <ProFormText.Password
          name="password"
          fieldProps={{ size: 'large', prefix: <LockOutlined /> }}
          placeholder="Пароль"
          rules={[{ required: true, message: 'Введите пароль' }]}
        />
      </LoginForm>
    </div>
  )
}
