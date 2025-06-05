import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api.jsx'
import {
  FaArrowDown,
  FaArrowUp,
  FaSyncAlt,
  FaSearch,
  FaHistory,
  FaChevronDown,
  FaChevronUp,
} from 'react-icons/fa'

export default function Prediction() {
  const navigate = useNavigate()

  const [district, setDistrict] = useState('')

  const [history, setHistory] = useState([])
  const [showAll, setShowAll] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(true)
  const [errorHistory, setErrorHistory] = useState('')

  const [predId, setPredId] = useState('')
  const [predDetail, setPredDetail] = useState(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [errorDetail, setErrorDetail] = useState('')

  const [loadingFree, setLoadingFree] = useState(false)
  const [loadingPaid, setLoadingPaid] = useState(false)
  const [errorPredict, setErrorPredict] = useState('')

  const loadHistory = async (limit) => {
    setLoadingHistory(true)
    setErrorHistory('')
    try {
      const body = limit != null ? { amount: limit } : {}
      const res = await api.post('/prediction/history', body)
      setHistory(res.data.history || [])
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
    loadHistory(5)
  }, [navigate])

  const toggleShowAll = () => {
    if (showAll) {
      loadHistory(5)
      setShowAll(false)
    } else {
      loadHistory(null)
      setShowAll(true)
    }
  }

  const handleRefresh = () => {
    loadHistory(showAll ? null : 5)
    setErrorPredict('')
  }

  const handlePredictFree = async (e) => {
    e.preventDefault()
    setErrorPredict('')
    if (!district || isNaN(parseInt(district))) {
      setErrorPredict('Введите корректный номер района.')
      return
    }
    setLoadingFree(true)
    try {
      const res = await api.post('/prediction/nyc_free', {
        district: parseInt(district),
      })
      alert(`Задача отправлена. ID: ${res.data.id}`)
      setDistrict('')
      loadHistory(showAll ? null : 5)
    } catch (err) {
      if (err.response?.status === 401) {
        navigate('/login')
        return
      }
      setErrorPredict(err.response?.data?.detail || 'Ошибка отправки.')
    } finally {
      setLoadingFree(false)
    }
  }

  const handlePredictPaid = async (e) => {
    e.preventDefault()
    setErrorPredict('')
    if (!district || isNaN(parseInt(district))) {
      setErrorPredict('Введите корректный номер района.')
      return
    }
    setLoadingPaid(true)
    try {
      const res = await api.post('/prediction/nyc_cost', {
        district: parseInt(district),
      })
      alert(`Платная задача отправлена. ID: ${res.data.id}`)
      setDistrict('')
      loadHistory(showAll ? null : 5)
    } catch (err) {
      if (err.response?.status === 401) {
        navigate('/login')
        return
      }
      setErrorPredict(err.response?.data?.detail || 'Ошибка платного запроса.')
    } finally {
      setLoadingPaid(false)
    }
  }

  const handleFetchById = async (e) => {
    e.preventDefault()
    setPredDetail(null)
    setErrorDetail('')
    if (!predId || isNaN(parseInt(predId))) {
      setErrorDetail('Введите корректный ID.')
      return
    }
    setLoadingDetail(true)
    try {
      const res = await api.get(`/prediction/${parseInt(predId)}`)
      setPredDetail(res.data)
      setPredId('')
    } catch (err) {
      if (err.response?.status === 401) {
        navigate('/login')
        return
      }
      if (err.response?.status === 404) {
        setErrorDetail('Предсказание не найдено.')
      } else {
        setErrorDetail('Не удалось получить данные.')
      }
    } finally {
      setLoadingDetail(false)
    }
  }

  if (loadingHistory) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gradient-to-br from-green-50 to-white">
        <h2 className="text-xl font-medium text-gray-700 animate-pulse">Загрузка истории...</h2>
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
    <div className="flex justify-center items-center px-4 bg-gradient-to-br from-green-50 to-white py-8">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-xl animate-fadeIn">
        {/* Заголовок */}
        <div className="flex justify-center items-center mb-6">
          <FaHistory className="text-blue-600 w-6 h-6 mr-2 animate-pulse" />
          <h1 className="text-3xl font-extrabold text-gray-800">Прогноз спроса</h1>
        </div>

        <form className="flex flex-col items-center mb-8" onSubmit={handlePredictFree}>
          <input
            type="number"
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            placeholder="Номер района (NYC)"
            className="w-48 border border-gray-300 px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-300 mb-4"
          />
          <div className="flex space-x-4">
            <button
              type="submit"
              disabled={loadingFree}
              className={`flex items-center bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-500 transition-colors ${
                loadingFree ? 'opacity-60 cursor-not-allowed' : ''
              }`}
            >
              {loadingFree ? 'Запрос...' : 'Бесплатно'}
              <FaArrowUp className="ml-2" />
            </button>
            <button
              type="button"
              onClick={handlePredictPaid}
              disabled={loadingPaid}
              className={`flex items-center bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-500 transition-colors ${
                loadingPaid ? 'opacity-60 cursor-not-allowed' : ''
              }`}
            >
              {loadingPaid ? 'Оплата...' : 'Платно'}
              <FaArrowDown className="ml-2" />
            </button>
          </div>
          {errorPredict && <p className="text-red-500 mt-3">{errorPredict}</p>}
        </form>

        <form
          className="flex flex-col items-center mb-8"
          onSubmit={handleFetchById}
        >
          <input
            type="number"
            value={predId}
            onChange={(e) => setPredId(e.target.value)}
            placeholder="Получить по ID"
            className="w-48 border border-gray-300 px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-300 mb-4"
          />
          <button
            type="submit"
            disabled={loadingDetail}
            className={`flex items-center bg-green-600 text-white px-4 py-2 rounded hover:bg-green-500 transition-colors ${
              loadingDetail ? 'opacity-60 cursor-not-allowed' : ''
            }`}
          >
            {loadingDetail ? 'Загрузка...' : 'Показать'}
            <FaSearch className="ml-2" />
          </button>
          {errorDetail && <p className="text-red-500 mt-3">{errorDetail}</p>}
        </form>

        {predDetail && (
          <div className="bg-gray-50 rounded-lg shadow-inner px-6 py-4 mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-3">
              Предсказание ID: {predDetail.id}
            </h2>
            <div className="space-y-1 text-gray-700">
              <p>
                <span className="font-medium">Модель:</span> {predDetail.model}
              </p>
              <p>
                <span className="font-medium">Город:</span> {predDetail.city}
              </p>
              <p>
                <span className="font-medium">Район:</span> {predDetail.district}
              </p>
              <p>
                <span className="font-medium">Час:</span> {predDetail.hour}
              </p>
              <p>
                <span className="font-medium">Стоимость:</span>{' '}
                {predDetail.cost.toFixed(2)}₽
              </p>
              <p>
                <span className="font-medium">Статус:</span> {predDetail.status}
              </p>
              <p>
                <span className="font-medium">Результат:</span>{' '}
                {predDetail.result || '—'}
              </p>
              <p>
                <span className="font-medium">Время:</span> {predDetail.timestamp}
              </p>
            </div>
          </div>
        )}

        <div>
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-xl font-semibold text-gray-800">История</h2>
            <button
              onClick={toggleShowAll}
              className="flex items-center text-gray-600 hover:text-gray-800 transition-colors"
            >
              {showAll ? (
                <>
                  Скрыть <FaChevronUp className="ml-1" />
                </>
              ) : (
                <>
                  Показать всё <FaChevronDown className="ml-1" />
                </>
              )}
            </button>
          </div>
          <div className="flex justify-center mb-4">
            <button
              onClick={handleRefresh}
              className="flex items-center bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-500 transition-colors"
            >
              <FaSyncAlt className="mr-2 animate-spin-slow" />
              Обновить историю
            </button>
          </div>
          <ul className="space-y-3">
            {history.length === 0 ? (
              <li className="text-center text-gray-500">Нет записей</li>
            ) : (
              history.map((item) => (
                <li key={item.id} className="
        bg-white
        rounded-xl
        shadow-sm
        hover:shadow-md
        transition-shadow duration-200
        p-4
        flex flex-col md:flex-row md:justify-between
        space-y-2 md:space-y-0 md:space-x-4
      ">
                  <div className="flex-1">
                    <div className="flex items-center mb-1">
                      <span className="font-semibold text-gray-700 mr-2">ID: {item.id}</span>
                      <span className="text-gray-600">— Район: {item.district}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Результат:</span>{' '}
                      <span className="text-gray-600">
              {Array.isArray(item.result) ? `[${item.result.join(', ')}]` : item.result}
            </span>
                    </div>
                  </div>

                  <div className="flex flex-col items-start md:items-end justify-center text-right">
                    <span className="text-blue-600 font-semibold">Статус: <span
                      className="font-normal text-gray-800">{item.status}</span></span>
                    <span className="text-gray-500 text-sm mt-1">{item.timestamp}</span>
                  </div>
                </li>
              ))
            )}
          </ul>
        </div>
      </div>
    </div>
  )
}
