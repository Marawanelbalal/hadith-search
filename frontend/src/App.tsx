import { MemoryRouter, Routes, Route } from 'react-router-dom';
import Footer from './components/Footer';
import Header from './components/Header';
import BenchmarksPage from './pages/BenchmarksPage';
import DevModePage from './pages/DevModePage';
import HomePage from './pages/HomePage';
import LoadingPage from './pages/LoadingPage';
import ResultsPage from './pages/ResultsPage';

const App = () => {
  return (
    <MemoryRouter>
      <div className="flex flex-col min-h-screen bg-background text-on-background font-body-main text-body-main antialiased">
        <Header />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/dev" element={<DevModePage />} />
          <Route path="/benchmarks" element={<BenchmarksPage />} />
          <Route path="/loading" element={<LoadingPage />} />
        </Routes>
        <Footer />
      </div>
    </MemoryRouter>
  );
};

export default App;
