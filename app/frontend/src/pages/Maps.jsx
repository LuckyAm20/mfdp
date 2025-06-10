// src/pages/Maps.jsx
import React, { useState } from 'react'

const images = [
  '/maps/map1.jpg',
  '/maps/map2.jpg',
  '/maps/map3.jpg',
  '/maps/map4.jpg',
  '/maps/map5.jpg',
]

export default function Maps() {
  const [lightbox, setLightbox] = useState({ open: false, src: '' })

  const openLightbox = (src) => setLightbox({ open: true, src })
  const closeLightbox = () => setLightbox({ open: false, src: '' })

  return (
    <div className="min-h-full bg-green-50 py-12 px-4">
      <h1 className="text-4xl font-extrabold text-center mb-8">Карты зон такси</h1>
      <div className="max-w-6xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
        {images.map((src, idx) => (
          <div
            key={idx}
            className="overflow-hidden rounded-xl shadow-lg transform hover:scale-105 transition-transform bg-white cursor-pointer"
            onClick={() => openLightbox(src)}
          >
            <img
              src={src}
              alt={`map ${idx + 1}`}
              className="w-full h-80 object-cover"
            />
          </div>
        ))}
      </div>

      {lightbox.open && (
        <div
          className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50 p-4"
          onClick={closeLightbox}
        >
          <img
            src={lightbox.src}
            alt="full-screen map"
            className="max-h-full max-w-full rounded-lg shadow-2xl"
          />
          <button
            onClick={closeLightbox}
            className="absolute top-6 right-6 text-white bg-red-600 hover:bg-red-700 rounded-full p-2 focus:outline-none"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  )
}
