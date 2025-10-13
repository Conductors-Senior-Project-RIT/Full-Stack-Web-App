import React from 'react';
import './css/Home.css';
import nys_trains from '../media/images/nys_trains.png';

const Home = () => {
  return (
    <div className="home-container">
      <h1>Welcome to TrackSense</h1>
      <img src={nys_trains} alt="TrackSense Overview" className="home-image" />
    </div>
  );
};

export default Home;