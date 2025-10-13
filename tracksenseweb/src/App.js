import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import './App.css';
import NavBar from './components/NavBar';
import AboutUs from './components/AboutUs';
import Login from './components/Login';
import Data from './components/Data';
import Home from './components/Home';

const App = () => {
  const location = useLocation();

  // Determine the background class based on the current route
  const getBackgroundClass = () => {
    switch (location.pathname) {
      case '/':
        return 'bg-home';
      case '/data':
        return 'bg-data';
      case '/aboutus':
        return 'bg-aboutus';
      case '/login':
        return 'bg-login';
      default:
        return '';
    }
  };

  return (
    <div className={`App ${getBackgroundClass()}`}>
      <NavBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/tracksense/" element={<Home />} />
        <Route path="/tracksense" element={<Home />} />
        <Route path="/data" element={<Data />} />
        <Route path="/aboutus" element={<AboutUs />} />
        <Route path="/login" element={<Login />} />
      </Routes>
    </div>
  );
};

const AppWrapper = () => (
  <Router>
    <App />
  </Router>
);

export default AppWrapper;