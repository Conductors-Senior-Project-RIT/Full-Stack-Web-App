import React, { useEffect, useState, useRef } from 'react';
import './css/Station.css';
import config from '../config';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';

const Station = ({ station, image, locationImage }) => {
  // State to store EOT records fetched from the backend
  const [Records, setRecords] = useState([]);
  const [popUpRecord, setPopUpRecords] = useState([]);
  // State to store HOT records fetched from the backend
  const [hotRecords, setHotRecords] = useState([]);
  // State to control the visibility of the dropdown
  const [showDropdown, setShowDropdown] = useState(false);
  const [showEOTPopUp, setShowEOTPopUp] = useState(false);
  const [showHOTPopUp, setShowHOTPopUp] = useState(false);
  // State to get the last seen time for the station
  const [lastSeen, setLastSeen] = useState(null);

  // Ref for the dropdown container
  const dropdownRef = useRef(null);

  useEffect(() => {
    fetch(`${config.apiUrl}/station_online?station_name=${station}`)
      .then(response => response.json())
      .then(data => {
        setLastSeen(data.last_seen);
      })
      .catch(error => console.error("Error fetching timestamp:", error));
  }, []);

  // Function to handle the pin click event
  const handlePinClick = () => {
    fetch(`${config.apiUrl}/recent_activities?type=3&station_name=${station}&most_recent=0&timerange=12:00:00`)
      .then(response => response.json())
      .then(data => {
        setRecords(data || []);
        setShowDropdown(true);
      })
      .catch(error => {
        console.error('Error fetching train data:', error);
      });
  };

  const handleDetailClick = (typ, id_num) => {
    if (typ === "EOT") {
      fetch(`${config.apiUrl}/history?type=1&id=${id_num}`)
        .then(response => response.json())
        .then(data => {
          setPopUpRecords(data || []);
          setShowEOTPopUp(true);
        });
    } else if (typ === "HOT") {
      fetch(`${config.apiUrl}/history?type=2&id=${id_num}`)
        .then(response => response.json())
        .then(data => {
          setPopUpRecords(data || []);
          setShowHOTPopUp(true);
        });
    }
  };

  // Function to handle the close button click event
  const handleCloseClick = () => {
    setShowDropdown(false);
  };

  const handleClosePopUp = () => {
    setShowEOTPopUp(false);
    setShowHOTPopUp(false);
  };

  // Close dropdown when clicking outside of it
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const alt_text = `${station} Station Map`;

  return (
    <div className="Station-container">
      <h1>{station} Station</h1>
      <p>Last seen online: {lastSeen}</p>
      <div>
        <Modal
          show={showEOTPopUp}
          onHide={handleClosePopUp}
          backdrop="static"
          keyboard={false}
          dialogClassName="modal-top"
        >
          <Modal.Header>
            <Modal.Title>Additional Information</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            {popUpRecord.map((rec, index) => (
              <p key={index}>
                Date Recorded: {rec.date_rec}<br />
                Station Recorded at: {rec.station_name}<br />
                Train Symbol: {rec.symbol_name}<br />
                Unit Address: {rec.unit_addr}<br />
                Brake Pressure: {rec.brake_pressure}<br />
                Motion: {rec.motion}<br />
                Marker Light: {rec.marker_light}<br />
                Turbine: {rec.turbine}<br />
                Battery Condition: {rec.battery_cond}<br />
                Battery Charge: {rec.battery_charge}<br />
                Arm Status: {rec.arm_status}<br />
                Signal Strength: {rec.signal_strength}<br />
              </p>
            ))}
          </Modal.Body>
          <Modal.Footer>
            <Button variant='primary' onClick={() => handleClosePopUp()}>Close</Button>
          </Modal.Footer>
        </Modal>
      </div>
      <div className="map-container">
        <img src={image} alt={alt_text} className="map-image" />
        <img src={locationImage} alt="Pin" className="pin-image" onClick={() => handlePinClick()} role="button" />
        {showDropdown && (
          <div className="dropdown" ref={dropdownRef}>
            <button className="close-button" onClick={() => handleCloseClick()}>✖</button>
            <h2>Records at {station} Station</h2>
            <table border="1" className="table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Symbol</th>
                  <th>Locomotive Number</th>
                  <th>Signal Type</th>
                </tr>
              </thead>
              <tbody>
                {Array.isArray(Records) && Records.map((record, index) => (
                  <tr key={index} onClick={() => handleDetailClick(record.Data_type, record.id)}>
                    <td>{record.date_rec}</td>
                    <td>{record.symbol_id}</td>
                    <td>{record.engine_num_id}</td>
                    <td>{record.Data_type}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Station;