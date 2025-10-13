import React, { useState } from 'react';
import './css/Login.css';
import { useAuth } from './AuthContext';
import config from '../config';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');

  const handleResetRequest = (e) => {
    e.preventDefault();

    const user = { email };
    console.log(user)

    fetch(`${config.apiUrl}/forgot-password`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(user)
    })
      .then(response => response.json())
      .then(data => {
        console.log('Response data:', data)
        setMessage('A password reset request was sent to your email.')
      })
      .catch(error => {
        console.error('Error:', error);
        setMessage('Error logging in');
      });

    // const user = { email };
    // console.log(user);
    // fetch(`${config.apiUrl}/login`, {
    //   method: 'POST',
    //   headers: {
    //     'Content-Type': 'application/json'
    //   },
    //   body: JSON.stringify(user)
    // })
    //   .then(response => response.json())
    //   .then(data => {
    //     console.log('Response data:', data); 
    //     if (data.access_token) { 
    //       setMessage('Login successful');
    //       document.cookie = `token=${data.access_token}; path=/; max-age=${7 * 24 * 60 * 60}`;  // Store token in a cookie for 7 days
    //       login(); // Update the authentication state
    //     } else {
    //       setMessage(data.message);
    //     }
    //   })
    //   .catch(error => {
    //     console.error('Error:', error);
    //     setMessage('Error logging in');
    //   });

    // Send request to send user an email with a reset link
    // Along with that, store a secure token in the database with a certain expiration
  };

  return (
    <div className="login-container">
      <h2>Password Reset</h2>
      <form onSubmit={handleResetRequest}>
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
          <button type="submit">Reset Password</button>
        </div>
      </form>
      {message && <p>{message}</p>}
    </div>
  );
};

export default ForgotPassword;