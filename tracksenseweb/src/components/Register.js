import React, { useState } from 'react';
import './css/Register.css';
import config from '../config';

const Register = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showSuccessPopup, setShowSuccessPopup] = useState(false); // State for success popup
    const [showErrorPopup, setShowErrorPopup] = useState(false); // State for error popup
    const [errorMessage, setErrorMessage] = useState(''); // Error message content

    const handleRegister = (e) => {
        e.preventDefault();

        const user = { email, password };
        fetch(`${config.apiUrl}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(user)
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to register user');
                }
                return response.json();
            })
            .then(data => {
                if (data.message) {
                    setShowSuccessPopup(true); // Show success popup
                    setShowErrorPopup(false); // Hide error popup
                }
            })
            .catch(error => {
                console.error('Error:', error);
                setErrorMessage('Error creating user. Please try again.'); // Set error message
                setShowErrorPopup(true); // Show error popup
                setShowSuccessPopup(false); // Hide success popup
            });
    };

    return (
        <div className="register-container">
            <h2>Register</h2>
            {showSuccessPopup && (
                <div className="popup">
                    <p>Registration successful!</p>
                    <button onClick={() => setShowSuccessPopup(false)}>Close</button>
                </div>
            )}
            {showErrorPopup && (
                <div className="popup">
                    <p>{errorMessage}</p>
                    <button onClick={() => setShowErrorPopup(false)}>Close</button>
                </div>
            )}
            <form onSubmit={handleRegister}>
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
                    <button onClick={handleRegister}>Register</button>
                </div>
            </form>
        </div>
    );
};

export default Register;