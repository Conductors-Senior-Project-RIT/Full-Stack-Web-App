import React, { useState } from 'react';
import './css/Admin.css';
import config from '../config';

const Admin = () => {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState(1); // Default to Volunteer
  const [message, setMessage] = useState('');

  const handleElevate = () => {
    fetch(`${config.apiUrl}/elevate-user`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${document.cookie.split('token=')[1]}`
      },
      body: JSON.stringify({ email, role })
    })
      .then((response) => response.json())
      .then((data) => setMessage(data.message))
      .catch((error) => setMessage('Error elevating user'));
  };

  return (
    <div className="admin-container">
      <h2>Elevate User Role</h2>
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
        <label>Role:</label>
        <select value={role} onChange={(e) => setRole(Number(e.target.value))}>
          <option value={1}>Volunteer</option>
          <option value={2}>Regular User</option>
        </select>
      </div>
      <button onClick={handleElevate}>Elevate</button>
      {message && <p>{message}</p>}
    </div>
  );
};

export default Admin;