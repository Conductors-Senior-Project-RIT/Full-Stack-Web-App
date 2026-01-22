import React, { useState } from 'react';
import './css/Home.css';
import nys_trains from '../media/images/nys_trains.png';
import churchville_marker from '../media/images/blackpin.png';
import hornell_marker from '../media/images/blackpin.png';
import macedon_marker from '../media/images/blackpin.png';
import rotterdam_marker from '../media/images/blackpin.png';
import silversprings_marker from '../media/images/blackpin.png';
import fairport_marker from '../media/images/blackpin.png';
import pittsford_marker from '../media/images/blackpin.png';
import fairgrounds_marker from '../media/images/blackpin.png';

const Home = () => {
  const [hoveredStation, setHoveredStation] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });

  const handlePinClick = (station) => {
    window.location.href = `/${station}`;
  };

  const handleMouseEnter = (station, event) => {
    const rect = event.target.getBoundingClientRect();
    console.log(rect)
    setTooltipPosition({ top: rect.top - 25, left: rect.left + 25});
    setHoveredStation(station);
  };

  const handleMouseLeave = () => {
    setHoveredStation(null);
  };

  return (
    <div className="home-container">
      <h1>Follow That Fred™</h1>
      <div className="map-container">
        <img src={nys_trains} alt="Map" className="map-image" />
        <img
          src={fairport_marker}
          alt="Pin"
          className="location-image"
          style={{ position: "absolute", top: '38.8157%', left: '24.5908%', objectfit:"contain", width:25, height:25 }}
          onClick={() => handlePinClick('fairport')}
          onMouseEnter={(e) => handleMouseEnter('Fairport', e)}
          onMouseLeave={handleMouseLeave}
        />
        <img
          src={churchville_marker}
          alt="Pin"
          className="location-image"
          style={{position: "absolute", top: '38.6804%', left: '20.6628%', objectfit:"contain", width:25, height:25 }}
          onClick={() => handlePinClick('churchville')}
          onMouseEnter={(e) => handleMouseEnter('Churchville', e)}
          onMouseLeave={handleMouseLeave}
        />
        <img
          src={macedon_marker}
          alt="Pin"
          className="location-image"
          style={{ position: "absolute", top: '39.1979%', left: '25.9001%', objectfit:"contain", width:25, height:25 }}
          onClick={() => handlePinClick('macedon')}
          onMouseEnter={(e) => handleMouseEnter('Macedon', e)}
          onMouseLeave={handleMouseLeave}
        />
        <img
          src={rotterdam_marker}
          alt="Pin"
          className="location-image"
          style={{ position: "absolute", top: '45.5368%', left: '56.5057%', objectfit:"contain", width:25, height:25 }}
          onClick={() => handlePinClick('rotterdam')}
          onMouseEnter={(e) => handleMouseEnter('Rotterdam', e)}
          onMouseLeave={handleMouseLeave}
        />
        <img
          src={silversprings_marker}
          alt="Pin"
          className="location-image"
          style={{ position: "absolute", top: '47.2186%', left: '18.4533%', objectfit:"contain", width:25, height:25 }}
          onClick={() => handlePinClick('silver-springs')}
          onMouseEnter={(e) => handleMouseEnter('Silver Springs', e)}
          onMouseLeave={handleMouseLeave}
        />
        <img
          src={hornell_marker}
          alt="Pin"
          className="location-image"
          style={{ position: "absolute", top: '54.2043%', left: '22.2176%', objectfit:"contain", width:25, height:25 }}
          onClick={() => handlePinClick('hornell')}
          onMouseEnter={(e) => handleMouseEnter('Hornell', e)}
          onMouseLeave={handleMouseLeave}
        />
        <img
          src={pittsford_marker}
          alt="Pin"
          className="location-image"
          style={{ position: "absolute", top: '40%', left: '23%', objectfit:"contain", width:25, height:25 }}
          onClick={() => handlePinClick('pittsford')}
          onMouseEnter={(e) => handleMouseEnter('Pittsford', e)}
          onMouseLeave={handleMouseLeave}
        />
        <img
          src={fairgrounds_marker}
          alt="Pin"
          className="location-image"
          style={{ position: "absolute", top: '38.25%', left: '34.85%', objectfit:"contain", width:25, height:25 }}
          onClick={() => handlePinClick('fairgrounds')}
          onMouseEnter={(e) => handleMouseEnter('Fairgrounds', e)}
          onMouseLeave={handleMouseLeave}
        />
      </div>
      {hoveredStation && (
          <div
            className="station-tooltip"
            style={{ top: tooltipPosition.top, left: tooltipPosition.left }}
          >
            {hoveredStation}
          </div>
        )}
    </div>
  );
};

export default Home;