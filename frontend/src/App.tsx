import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import MainPage from './pages/MainPage';
import './App.css';

const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true';

function App() {
  const token = localStorage.getItem('token');
  const isAuthenticated = DEV_MODE || !!token;

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/auth/callback"
          element={<AuthCallback />}
        />
        <Route
          path="/"
          element={isAuthenticated ? <MainPage /> : <Navigate to="/login" />}
        />
      </Routes>
    </BrowserRouter>
  );
}

function AuthCallback() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get('token');
  if (token) {
    localStorage.setItem('token', token);
  }
  window.location.href = '/';
  return null;
}

export default App;
