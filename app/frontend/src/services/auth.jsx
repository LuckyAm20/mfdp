import api from './api';

const TOKEN_KEY = 'access_token';

export function setAuthHeader(token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

export function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
  setAuthHeader(token);
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function removeToken() {
  localStorage.removeItem(TOKEN_KEY);
  delete api.defaults.headers.common['Authorization'];
}

export async function login(username, password) {
  const res = await api.post('/auth/login', { username, password });
  return res.data;
}

export async function register(username, password) {
  const res = await api.post('/auth/register', { username, password });
  return res.data;
}

export async function fetchCurrentUser() {
  const res = await api.get('/auth/me');
  return res.data;
}
