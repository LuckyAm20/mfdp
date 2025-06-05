import React from 'react'
import { Link, useNavigate } from 'react-router-dom'

export default function Navbar() {
  const navigate = useNavigate()
  const token = localStorage.getItem('access_token')

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    navigate('/')
  }

  return (
    <nav className="h-16 bg-green-600 text-white px-4 flex items-center justify-between shadow-md sticky top-0 z-10">
      <div className="flex items-center space-x-4">
        <Link to="/" className="text-lg font-semibold hover:text-green-200 transition-colors">
          OpenTaxiForecast
        </Link>
        {token && (
          <>
            <Link to="/info" className="hover:text-green-200 transition-colors">
                Инфо
            </Link>
            <Link to="/balance" className="hover:text-green-200 transition-colors">
              Баланс
            </Link>
            <Link to="/prediction" className="hover:text-green-200 transition-colors">
              Предсказание
            </Link>
          </>
        )}
      </div>

      <div className="flex items-center space-x-4">
        {token ? (
          <button
            onClick={handleLogout}
            className="bg-green-800 hover:bg-green-900 px-3 py-1 rounded-lg transition shadow-sm hover:shadow-md"
          >
            Выйти
          </button>
        ) : (
          <>
            <Link
              to="/login"
              className="border border-white rounded px-3 py-1 hover:bg-green-700 hover:border-green-300 transition-colors"
            >
              Войти
            </Link>
            <Link
              to="/register"
              className="border border-white rounded px-3 py-1 hover:bg-green-700 hover:border-green-300 transition-colors"
            >
              Зарегистрироваться
            </Link>
          </>
        )}
      </div>
    </nav>
  )
}
