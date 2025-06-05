import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api.jsx'
import { fetchCurrentUser } from '../services/auth'
import {
  FaArrowDown,
  FaArrowUp,
  FaSyncAlt,
  FaWallet,
  FaAngleDown,
  FaAngleUp,
} from 'react-icons/fa'

export default function Balance() {
  const navigate = useNavigate()

  const [history, setHistory] = useState([])
  const [showAll, setShowAll] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(true)
  const [errorHistory, setErrorHistory] = useState('')

  const [topUpAmount, setTopUpAmount] = useState('')
  const [loadingTopUp, setLoadingTopUp] = useState(false)
  const [errorTopUp, setErrorTopUp] = useState('')

  const [selectedStatus, setSelectedStatus] = useState('silver')
  const [loadingPurchase, setLoadingPurchase] = useState(false)
  const [errorPurchase, setErrorPurchase] = useState('')
  const [successPurchase, setSuccessPurchase] = useState('')

  const [currentBalance, setCurrentBalance] = useState(null)

  const loadHistory = async (limit) => {
    setLoadingHistory(true)
    setErrorHistory('')
    try {
      const body = limit != null ? { amount: limit } : {}
      const res = await api.post('/balance/history', body)
      setHistory(res.data.history)
    } catch (err) {
      if (err.response?.status === 401) {
        navigate('/login')
        return
      }
      setErrorHistory('Не удалось загрузить историю.')
      setHistory([])
    } finally {
      setLoadingHistory(false)
    }
  }

  useEffect(() => {
    const initialize = async () => {
      try {
        const userData = await fetchCurrentUser()
        setCurrentBalance(userData.balance)
      } catch (err) {
        if (err.response?.status === 401) {
          navigate('/login')
          return
        }
        console.error('Ошибка при получении данных пользователя:', err)
      } finally {
        loadHistory(5)
      }
    }
    initialize()
  }, [navigate])

  const toggleShowAll = () => {
    if (showAll) {
      loadHistory(5)
      setShowAll(false)
    } else {
      loadHistory(1000)
      setShowAll(true)
    }
  }

  const handleRefresh = () => {
    loadHistory(showAll ? 1000 : 5)
    setSuccessPurchase('')
    setErrorPurchase('')
  }

  const handleTopUp = async (e) => {
    e.preventDefault()
    setErrorTopUp('')
    setSuccessPurchase('')
    if (!topUpAmount || isNaN(parseFloat(topUpAmount))) {
      setErrorTopUp('Введите корректную сумму.')
      return
    }
    setLoadingTopUp(true)
    try {
      const res = await api.post('/balance/top_up', {
        amount: parseFloat(topUpAmount),
      })
      setCurrentBalance(res.data.new_balance)
      setTopUpAmount('')
      loadHistory(showAll ? 1000 : 5)
    } catch (err) {
      if (err.response?.status === 401) {
        navigate('/login')
        return
      }
      setErrorTopUp(err.response?.data?.detail || 'Ошибка пополнения.')
    } finally {
      setLoadingTopUp(false)
    }
  }

  const handlePurchase = async (e) => {
    e.preventDefault()
    setErrorPurchase('')
    setSuccessPurchase('')
    setLoadingPurchase(true)
    try {
      const res = await api.post('/balance/purchase', {
        status: selectedStatus,
      })
      setSuccessPurchase(
        `Статус "${res.data.status}" активен до ${res.data.status_date_end}. Баланс: ${res
          .data.remaining_balance.toFixed(2)}₽`
      )
      setCurrentBalance(res.data.remaining_balance)
      loadHistory(showAll ? 1000 : 5)
    } catch (err) {
      if (err.response?.status === 401) {
        navigate('/login')
        return
      }
      setErrorPurchase(err.response?.data?.detail || 'Не удалось продлить статус.')
    } finally {
      setLoadingPurchase(false)
    }
  }

  if (loadingHistory) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gradient-to-br from-green-50 to-white">
        <h2 className="text-xl font-medium text-gray-700 animate-pulse">Загрузка...</h2>
      </div>
    )
  }

  if (errorHistory) {
    return (
      <div className="flex flex-col justify-center items-center min-h-screen bg-gradient-to-br from-green-50 to-white px-4">
        <h2 className="text-xl font-medium text-red-500 mb-4">{errorHistory}</h2>
        <button
          onClick={() => navigate('/login')}
          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-500"
        >
          Войти
        </button>
      </div>
    )
  }

  return (
    <div className="flex justify-center items-start pt-4 px-4 bg-gradient-to-br from-green-50 to-white min-h-screen">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-lg animate-fadeIn">
        <div className="flex justify-center items-center mb-6">
          <FaWallet className="text-green-600 w-6 h-6 mr-2 animate-pulse" />
          <h1 className="text-3xl font-extrabold text-gray-800">Ваш баланс</h1>
        </div>

        <div className="flex justify-center items-baseline mb-6 space-x-2">
          <span className="text-5xl font-bold text-gray-900">
            {currentBalance != null ? currentBalance.toFixed(2) : '0.00'}
          </span>
          <span className="text-2xl text-gray-700">₽</span>
        </div>

        <form onSubmit={handleTopUp} className="flex justify-center mb-6 space-x-2">
          <input
            type="number"
            step="0.01"
            value={topUpAmount}
            onChange={(e) => setTopUpAmount(e.target.value)}
            placeholder="Сумма"
            className="w-32 border border-gray-300 px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-green-300"
          />
          <button
            type="submit"
            disabled={loadingTopUp}
            className={`flex items-center bg-green-600 text-white px-4 py-2 rounded hover:bg-green-500 transition-colors ${
              loadingTopUp ? 'opacity-60 cursor-not-allowed' : ''
            }`}
          >
            <FaArrowUp className="mr-2" />
            {loadingTopUp ? 'Пополняем...' : 'Пополнить'}
          </button>
        </form>
        {errorTopUp && <p className="text-center text-red-500 mb-4">{errorTopUp}</p>}

        <form onSubmit={handlePurchase} className="mb-6">
          <div className="flex justify-center items-center space-x-2 mb-2">
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="border border-gray-300 px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-green-300"
            >
              <option value="silver">Silver</option>
              <option value="gold">Gold</option>
              <option value="diamond">Diamond</option>
            </select>
            <button
              type="submit"
              disabled={loadingPurchase}
              className={`flex items-center bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-500 transition-colors ${
                loadingPurchase ? 'opacity-60 cursor-not-allowed' : ''
              }`}
            >
              <FaArrowDown className="mr-2" />
              {loadingPurchase ? 'Обрабатываем...' : 'Купить/Продлить'}
            </button>
          </div>
          {errorPurchase && (
            <p className="text-center text-red-500 mb-2">{errorPurchase}</p>
          )}
          {successPurchase && (
            <p className="text-center text-green-700 mb-2">{successPurchase}</p>
          )}
        </form>

        <div className="flex justify-center mb-4">
          <button
            onClick={handleRefresh}
            className="flex items-center bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-500 transition-colors"
          >
            <FaSyncAlt className="mr-2 animate-spin-slow" />
            Обновить историю
          </button>
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-xl font-semibold text-gray-800">История</h2>
            <button
              onClick={toggleShowAll}
              className="flex items-center text-gray-600 hover:text-gray-800 transition-colors"
            >
              {showAll ? (
                <>
                  Скрыть <FaAngleUp className="ml-1" />
                </>
              ) : (
                <>
                  Показать всё <FaAngleDown className="ml-1" />
                </>
              )}
            </button>
          </div>
          {history.length === 0 ? (
            <p className="text-center text-gray-500">Нет записей</p>
          ) : (
            <ul className="space-y-2 max-h-58 overflow-y-auto pr-2">
              {history.map((item, index) => (
                <li
                  key={index}
                  className="
                    flex justify-between items-center
                    bg-gray-50
                    rounded-lg
                    px-4 py-2
                    shadow-sm
                    hover:shadow-md
                    transition-shadow
                    duration-200
                  "
                >
                  <span className="text-gray-700 text-sm">{item.timestamp}</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-600 text-sm">{item.description}</span>
                    <span className="font-medium text-gray-800">
                      {item.amount >= 0 ? (
                        <FaArrowUp className="inline text-green-600 mr-1" />
                      ) : (
                        <FaArrowDown className="inline text-red-600 mr-1" />
                      )}
                      {Math.abs(item.amount).toFixed(2)}₽
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
