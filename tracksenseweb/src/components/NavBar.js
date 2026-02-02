import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from './AuthContext';
import './css/NavBar.css';

const NavBar = () => {
    const { isAuthenticated, userRole, logout } = useAuth(); // Access userRole from useAuth

    return (
        <nav>
            <ul>
                <li><Link to="/tracksense">Home</Link></li>
                <li><Link to="/eot-data">EOT Data</Link></li>
                <li><Link to="/hot-data">HOT Data</Link></li>
                <li><Link to="/aboutus">About Us</Link></li>
                {!isAuthenticated && (
                    <>
                        <li><Link to="/login">Log In</Link></li>
                        <li><Link to="/register">Register</Link></li>
                    </>
                )}
                {isAuthenticated && (
                    <>
                        {userRole <= 1 && ( // Only show verification link for Volunteers (1) and Superusers (0)
                            <li><Link to="/verify-eot">Verify EOT</Link></li>
                        )}{userRole <= 1 && ( // Only show verification link for Volunteers (1) and Superusers (0)
                            <li><Link to="/verify-hot">Verify HOT</Link></li>
                        )}
                        {userRole === 0 && ( // Only show Superuser link for Superusers (0)
                            <li><Link to="/superuser">Superuser</Link></li>
                        )}
                        <li><Link to="/options">Options</Link></li>
                        <li><button onClick={logout} className="logout-button">Log Out</button></li>
                    </>
                )}
            </ul>
        </nav>
    );
};

export default NavBar;