import React from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import NavBar from './components/NavBar';
import AboutUs from './components/AboutUs';
import Login from './components/Login';
import Register from './components/Register';
import Data from './components/Data';
import Home from './components/Home';
import VerifyEOT from './components/VerifyEOT';
import VerifyHOT from './components/VerifyHOT';
import Fairport from './components/Fairport';
import Churchville from './components/Churchville';
import Macedon from './components/Macedon';
import Rotterdam from './components/Rotterdam';
import SilverSprings from './components/SilverSprings';
import Hornell from './components/Hornell';
import Pittsford from './components/Pittsford';
import Fairgrounds from './components/Fairgrounds';
import { AuthProvider } from './components/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import ForgotPassword from './components/ForgotPassword';
import ResetPassword from './components/ResetPassword';
import Options from './components/Options';
import Superuser from './components/SuperUser';
import HotData from './components/HOT_Data';

//reorder to the right order

const App = () => {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <NavBar />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/tracksense/" element={<Home />} />
            <Route path="/tracksense" element={<Home />} />
            <Route path="/aboutus" element={<AboutUs />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/eot-data" element={<ProtectedRoute element={Data} requiredRole={2}/>} />
            <Route path="/hot-data" element={<ProtectedRoute element={HotData} requiredRole={2}/>} />
            <Route path="/verify-eot" element={<ProtectedRoute element={VerifyEOT} requiredRole={1}/>} />
            <Route path="/verify-hot" element={<ProtectedRoute element={VerifyHOT} requiredRole={1}/>} />
            <Route path="/fairport" element={<Fairport />} />
            <Route path="/churchville" element={<Churchville />} />
            <Route path="/macedon" element={<Macedon />} />
            <Route path="/rotterdam" element={<Rotterdam />} />
            <Route path="/silver-springs" element={<SilverSprings />} />
            <Route path="/hornell" element={<Hornell />} />
            <Route path="/pittsford" element={<Pittsford />} />
            <Route path="/fairgrounds" element={<Fairgrounds />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/options" element={<ProtectedRoute element={Options} requiredRole={2} />} />
            <Route path="/Superuser" element={<ProtectedRoute element={Superuser} requiredRole={0} />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
};

export default App;