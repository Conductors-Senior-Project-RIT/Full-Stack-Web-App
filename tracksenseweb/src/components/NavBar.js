import React from 'react';
import { Link } from 'react-router-dom';
import './css/NavBar.css';

const NavBar = () => {
    return (
        <nav>
            <ul>
                <li><Link to="/tracksense">Home</Link></li>
                <li><Link to="/data">Historical Data</Link></li>
                <li><Link to="/aboutus">About Us</Link></li>
                <li><Link to="/login">Log In</Link></li>
            </ul>
        </nav>
    );
};

export default NavBar;