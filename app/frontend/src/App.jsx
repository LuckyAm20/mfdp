import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Balance from './pages/Balance'
import Prediction from './pages/Prediction'
import Info from './pages/Info'

import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'

export default function App() {
  return (
    <BrowserRouter>
      <div className="h-screen flex flex-col">
        <Navbar />
        <div className="flex-1 overflow-auto">
          <Routes>
            <Route
              path="/"
              element={
                <div className="h-full overflow-hidden">
                  <Home />
                </div>
              }
            />

            <Route path="/login" element={<div className="h-full overflow-hidden"><Login/></div>} />

            <Route path="/register" element={<div className="h-full overflow-hidden"><Register/></div>} />

            <Route
              path="/balance"
              element={
                <ProtectedRoute>
                  <Balance />
                </ProtectedRoute>
              }
            />

            <Route
              path="/prediction"
              element={
                <ProtectedRoute>
                  <Prediction />
                </ProtectedRoute>
              }
            />

            <Route
              path="/info"
              element={
                <ProtectedRoute>
                    <Info/>
                </ProtectedRoute>
              }
            />

            <Route
              path="*"
              element={
                  <Home />
              }
            />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  )
}
