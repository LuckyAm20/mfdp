import React from 'react'
import { Link } from 'react-router-dom'
import Logo from '../assets/logo_v1.png'

export default function Home() {
  return (
    <div className="h-full w-full flex flex-col items-center justify-center bg-green-50 text-gray-900 px-4">
      <div className="w-full max-w-2xl text-center space-y-6">
        <div className="flex justify-center">
          <img
            src={Logo}
            alt="OpenTaxiForecast Logo"
            draggable={false}
            onContextMenu={(e) => e.preventDefault()}
            className="
              h-64 w-64
              rounded-full
              shadow-2xl
              animate-bounce
              transition-transform
              hover:scale-105
            "
          />
        </div>

        <h1 className="text-5xl font-bold">OpenTaxiForecast</h1>

        <p className="text-lg">
          Добро пожаловать в <strong>OpenTaxiForecast</strong>! Здесь Вы можете
          спрогнозировать спрос на такси по районам города в режиме онлайн.
        </p>

        <p className="text-md text-gray-700">
          Чтобы начать работу с приложением, пожалуйста, зарегистрируйтесь или
          войдите в систему.
        </p>

        <Link
          to="/login"
          className="
            inline-block
            bg-green-500 hover:bg-green-600
            focus:ring-2 focus:ring-green-300
            text-white font-semibold
            py-3 px-8
            rounded-lg
            shadow-md hover:shadow-lg
            transition transform hover:-translate-y-0.5
          "
        >
          Зарегистрироваться / Войти
        </Link>
      </div>
    </div>
  )
}
