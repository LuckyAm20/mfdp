import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchCurrentUser } from '../services/auth'
import { FaUserCircle, FaCoins, FaCertificate } from 'react-icons/fa'
import '../App.css'

export default function Info() {
  const [userInfo, setUserInfo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    async function loadUser() {
      try {
        const data = await fetchCurrentUser()
        setUserInfo(data)
      } catch (err) {
        if (err.response?.status === 401) {
          navigate('/login')
          return
        }
        console.error('Ошибка при получении данных:', err)
        setError('Не удалось загрузить информацию о пользователе.')
      } finally {
        setLoading(false)
      }
    }
    loadUser()
  }, [navigate])

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gradient-to-br from-green-50 to-white">
        <h2 className="text-xl font-medium text-gray-700 animate-pulse">
          Загрузка...
        </h2>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gradient-to-br from-green-50 to-white">
        <h2 className="text-xl font-medium text-red-500">{error}</h2>
      </div>
    )
  }

  if (!userInfo) return null

  const getStatusBadgeClass = (status) => {
    switch ((status || '').toLowerCase()) {
      case 'bronze':
        return 'bg-amber-200 text-amber-800'
      case 'silver':
        return 'bg-gray-200 text-gray-800'
      case 'gold':
        return 'bg-yellow-200 text-yellow-800'
      case 'platinum':
        return 'bg-indigo-200 text-indigo-800'
      default:
        return 'bg-green-200 text-green-800'
    }
  }

  return (
    <div className="flex justify-center items-start pt-20 px-4 bg-gradient-to-br from-green-50 to-white min-h-screen">
      <div
        className="
          bg-white
          rounded-2xl
          shadow-xl
          hover:shadow-2xl
          transition-shadow
          duration-300
          p-8
          w-full
          max-w-lg
          animate-fadeIn
        "
      >
        <div className="flex justify-center items-center mb-6">
          <FaUserCircle className="text-green-600 text-5xl mr-2 animate-pulse" />
          <h1 className="text-3xl font-extrabold text-gray-800">
            Личный кабинет
          </h1>
        </div>

        <div className="divide-y divide-gray-200">
          <div className="py-4 flex items-center">
            <FaUserCircle className="text-gray-500 text-xl mr-3" />
            <span className="font-semibold text-gray-600 flex-1">Логин:</span>
            <span className="text-gray-800">{userInfo.username}</span>
          </div>

          <div className="py-4 flex items-center">
            <FaCoins className="text-yellow-500 text-xl mr-3" />
            <span className="font-semibold text-gray-600 flex-1">Баланс:</span>
            <span
              className="
                inline-block
                px-3
                py-1
                text-sm
                font-medium
                rounded-full
                bg-yellow-100
                text-yellow-800
                animate-pulse
              "
            >
              {userInfo.balance.toFixed(2)} ₽
            </span>
          </div>

          <div className="py-4 flex items-center">
            <FaCertificate className="text-indigo-500 text-xl mr-3" />
            <span className="font-semibold text-gray-600 flex-1">Статус:</span>
            <span
              className={`
                inline-block
                px-3
                py-1
                text-sm
                font-medium
                rounded-full
                ${getStatusBadgeClass(userInfo.status)}
              `}
            >
              {userInfo.status || '—'}
            </span>
          </div>

          <div className="pt-4 flex items-center">
            <span className="font-semibold text-gray-600 flex-1">Статус&nbsp;до:</span>
            <span className="text-gray-800">
              {userInfo.status_date_end || '—'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
