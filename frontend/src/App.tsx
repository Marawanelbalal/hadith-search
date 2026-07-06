import { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './layouts/Layout';
import UserHomePage from './pages/UserHomePage';
import UserSearchPage from './pages/UserSearchPage';
import DevHomePage from './pages/DevHomePage';
import DevSearchPage from './pages/DevSearchPage';
import DevBenchmarkPage from './pages/DevBenchmarkPage';
import DevComparePage from './pages/DevComparePage';
import DevAnnotationPage from './pages/DevAnnotationPage';
import DevAnnotationSessionPage from './pages/DevAnnotationSessionPage';
import KvVerificationPage from './pages/KvVerificationPage';
import SigninPage from './pages/SigninPage';
import SignupPage from './pages/SignupPage';
import AnnotationGuidelinesPage from './pages/AnnotationGuidelinesPage';

const App = () => {
  const [mode, setMode] = useState(() => localStorage.getItem('app_mode') || 'user');
  const defaultPath = mode === 'dev' ? '/dev/' : '/user/';

  const handleSetMode = (newMode: string) => {
    localStorage.setItem('app_mode', newMode);
    setMode(newMode);
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to={defaultPath} replace />} />
        <Route path="/user" element={<Navigate to="/user/" replace />} />
        <Route path="/dev" element={<Navigate to="/dev/" replace />} />

        <Route path="/user/" element={<Layout mode={mode} setMode={handleSetMode} />}>
          <Route index element={<UserHomePage />} />
          <Route path="search" element={<UserSearchPage />} />
        </Route>

        <Route path="/dev/" element={<Layout mode={mode} setMode={handleSetMode} />}>
          <Route index element={<DevHomePage />} />
          <Route path="search" element={<DevSearchPage />} />
          <Route path="benchmark" element={<DevBenchmarkPage />} />
          <Route path="compare" element={<DevComparePage />} />
          <Route path="annotation" element={<DevAnnotationPage />} />
          <Route path="annotation/signin" element={<SigninPage />} />
          <Route path="annotation/signup" element={<SignupPage />} />
          <Route path="annotation/guidelines" element={<AnnotationGuidelinesPage />} />
          <Route path="annotation/:queryId" element={<DevAnnotationSessionPage />} />
          <Route path="kv-pairs" element={<KvVerificationPage />} />
        </Route>

        <Route path="*" element={<Navigate to={defaultPath} replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;