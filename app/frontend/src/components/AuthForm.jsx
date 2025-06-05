import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import axios from 'axios'

export default function AuthForm({ mode }) {
  const navigate = useNavigate()
  const [login, setLogin] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const isLogin = mode === 'login'
  const heading = isLogin ? 'Вход в систему' : 'Регистрация'
  const buttonText = isLogin ? 'Войти' : 'Зарегистрироваться'
  const apiUrl = isLogin ? '/api/v1/auth/login' : '/api/v1/auth/register'
  const altText = isLogin
    ? 'Нет аккаунта? Зарегистрироваться'
    : 'Уже есть аккаунт? Войти'
  const altLink = isLogin ? '/register' : '/login'

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    try {
      const response = await axios.post(
        apiUrl,
        {
          username: login,
          password: password,
        },
        { headers: { 'Content-Type': 'application/json' } }
      )

      const { access_token } = response.data
      localStorage.setItem('access_token', access_token)
      navigate('/info')
    } catch (err) {
      console.error(err)
      const msg =
        err.response?.data?.detail ||
        'Не удалось ' + (isLogin ? 'войти' : 'зарегистрироваться')
      setError(msg)
    }
  }

  return (
    <div className="min-h-screen flex items-start justify-center bg-green-50 px-4 pt-16">
      <div className="w-full max-w-md bg-white rounded-xl shadow-lg p-8">
        <h2 className="text-3xl font-extrabold text-gray-800 text-center mb-6">
          {heading}
        </h2>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="login"
              className="block text-gray-700 mb-1 font-medium"
            >
              Логин
            </label>
            <input
              id="login"
              type="text"
              value={login}
              onChange={(e) => setLogin(e.target.value)}
              required
              className="w-full px-4 py-2 rounded-lg bg-gray-100 border border-gray-300 text-gray-800 focus:outline-none focus:ring-2 focus:ring-green-400"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-gray-700 mb-1 font-medium"
            >
              Пароль
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-2 rounded-lg bg-gray-100 border border-gray-300 text-gray-800 focus:outline-none focus:ring-2 focus:ring-green-400"
            />
          </div>

          <button
            type="submit"
            className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-2 rounded-lg transition"
          >
            {buttonText}
          </button>
        </form>

        <p className="mt-6 text-center text-gray-600">
          <Link to={altLink} className="text-green-600 hover:underline">
            {altText}
          </Link>
        </p>
      </div>
    </div>
  )
}
