import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import './css/Login.css';
import config from '../config';
import notfound from '../media/images/notfound.png'

const NotFound = () => {
  const location = useLocation();

  return (
    <div className="login-container">
      <h2>PAGE <br/> NOT FOUND</h2>
      <img src={notfound} style={{ width: "300px" }}/>
    </div>
  );
};

export default NotFound;