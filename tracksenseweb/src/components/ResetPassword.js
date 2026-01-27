import React, { useEffect, useState } from 'react';
import './css/Register.css';
import config from '../config';
import { useSearchParams, useNavigate } from "react-router-dom";

const ResetPassword = () => {
    const [confirmPassword, setConfirmPassword] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    const [searchParams] = useSearchParams();
    const token = searchParams.get("token");
    const [isValid, setIsValid] = useState(null); // null = loading, true/false = result
    const navigate = useNavigate();

    const handlePasswordReset = (e) => {
        e.preventDefault();

        if (password !== confirmPassword) {
            setError("Passwords don't match.");
            setMessage('');
            return
        }

        const user = { password };
        fetch(`${config.apiUrl}/reset-password?token=${encodeURIComponent(token)}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(user)
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to change user password.');
                }
                return response.json();
            })
            .then(data => {
                if (data.message) {
                    setMessage(data.message); // Display success message
                    setError(''); // Clear any previous error
                }
            })
            .catch(error => {
                console.error('Error:', error);
                setError('Error creating user. Please try again.'); // Display error message
                setMessage(''); // Clear any previous success message
            });
    };

    useEffect(() => {
        const checkToken = async () => {
          if (!token) {
            navigate("/login");
            return;
          }
    
          try {
            const res = await fetch(`${config.apiUrl}/validate-reset-token?token=${encodeURIComponent(token)}`);
            if (res.ok) {
              setIsValid(true);
            } else {
              navigate("/login");
            }
          } catch (error) {
            console.error("Error validating token:", error);
            navigate("/login");
          }
        };
    
        checkToken();
      }, [token, navigate]);
    
      if (isValid === null) return <div>Loading...</div>;

    return (
        <div className="register-container">
            <h2>Reset Your Password</h2>
            <form onSubmit={handlePasswordReset}>
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
                    <label>Confirm Password:</label>
                    <input
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                    />
                </div>
                <div className="form-group">
                    <button onClick={handlePasswordReset}>Reset Password</button>
                </div>
            </form>
            {message && <p className="success-message">{message}</p>}
            {error && <p className="error-message">{error}</p>}
        </div>
    );
};

export default ResetPassword;