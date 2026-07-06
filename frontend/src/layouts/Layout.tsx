import { Outlet } from 'react-router-dom';
import Navbar from '../components/Navbar';

const Layout = ({ mode, setMode }: { mode: string; setMode: (mode: string) => void }) => {
  return (
    <div className="flex flex-col min-h-screen bg-background dark:bg-dark-background text-on-background dark:text-dark-on-background font-body-main text-body-main antialiased">
      <Navbar mode={mode} onModeChange={setMode} />
      <Outlet />
    </div>
  );
};

export default Layout;