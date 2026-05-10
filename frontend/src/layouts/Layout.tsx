import { Outlet } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const Layout = () => {
  return (
    <div className="flex flex-col min-h-screen bg-background dark:bg-dark-background text-on-background dark:text-dark-on-background font-body-main text-body-main antialiased">
      <Navbar />
      <Outlet />
      <Footer />
    </div>
  );
};

export default Layout;