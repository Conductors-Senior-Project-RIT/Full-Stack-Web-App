import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import './css/Login.css';
import { useAuth } from './AuthContext';
import config from '../config';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [showPopup, setShowPopup] = useState(false);
  const [successPopup, setSuccessPopup] = useState(false); // State for login success popup
  const { login } = useAuth();
  const location = useLocation();

  // Check for redirection query parameter and show popup if redirected
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('redirected') === 'true') {
      setShowPopup(true);
    }
  }, [location]);

  const handleLogin = async (e) => {
    e.preventDefault();

    const user = { email, password };

    try {
      const response = await fetch(`${config.apiUrl}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: "include",
        body: JSON.stringify(user),
      });
      const data = await response.json();

      if (response.ok) {
        await login();
        setSuccessPopup(true);
        window.location.href = "/";
      } else {
        setMessage('Error logging in');
      }
    } catch (error) {
      setMessage('Error logging in');
    }
  };

  return (
    <div className="login-container">
      <h2>Login</h2>
      {showPopup && (
        <div className="popup">
          <p>You need to log in to access this feature.</p>
          <button onClick={() => setShowPopup(false)}>Close</button>
        </div>
      )}
      {successPopup && (
        <div className="popup">
          <p>Login successful!</p>
          <button onClick={() => setSuccessPopup(false)}>Close</button>
        </div>
      )}
      <form onSubmit={handleLogin}>
        <div className="form-group">
          <label>Email:</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label>Password:</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <button onClick={handleLogin}>Login</button>
        </div>
        <a href="/forgot-password" className="forgot-password-link">
          Forgot password?
        </a>
      </form>
      {message && <p className="error-message">{message}</p>}
    </div>
  );
};

export default Login;