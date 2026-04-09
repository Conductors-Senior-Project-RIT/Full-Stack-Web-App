import React, { useEffect, useState, useRef } from 'react';
import './css/Station.css';
import config from '../config';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';

const Station = ({ station, image, locationImage }) => {
  // State to store EOT/HOT records fetched from the backend
  const [Records, setRecords] = useState([]);
  // States for popups
  const [popUpRecord, setPopUpRecords] = useState([]);
  const [showEOTPopUp, setShowEOTPopUp] = useState(false);
  const [showHOTPopUp, setShowHOTPopUp] = useState(false);
  // State to get the last seen time for the station
  const [lastSeen, setLastSeen] = useState(null);

  useEffect(() => {
    fetch(`${config.apiUrl}/station_online?station_name=${station}`)
      .then(response => response.json())
      .then(data => {
        setLastSeen(data.last_seen);
      })
      .catch(error => console.error("Error fetching timestamp:", error));
  });

  useEffect(() => {
    fetch(`${config.apiUrl}/recent_activities?station_name=${station}&most_recent=0&timerange=12:00:00`)
      .then(response => response.json())
      .then(data => {
        const records = [...data.reduce((map, item) => {
          const key = `${item.unit_addr}${item.locomotive_num}`;
          return map.has(key) ? map : map.set(key, item);
        }, new Map()).values()];
        setRecords(records || []);
      })
      .catch(error => {
        console.error('Error fetching train data:', error);
      });
  }, [])

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

  const handleClosePopUp = () => {
    setShowEOTPopUp(false);
    setShowHOTPopUp(false);
  };

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
      <div>
        <Modal
          show={showHOTPopUp}
          onHide={handleClosePopUp}
          backdrop="static"
          keyboard={false}
          dialogClassName='modal-top'
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
                Command: {rec.command}<br />
                Signal Strength: {rec.signal_strength}<br />
              </p>
            ))}
          </Modal.Body>
          <Modal.Footer>
            <Button variant='primary' onClick={() => handleClosePopUp()}>Close</Button>
          </Modal.Footer>
        </Modal>
      </div>
      <div className="itemgrid">
        <div className="map-container">
          <img src={image} alt={alt_text} className="map-image" />
          <img src={locationImage} alt="Pin" className="pin-image"/>
        </div>
        <div className="dropdown">
          <h2>Records at {station} Station</h2>
          <table border="1" className="table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Symbol</th>
                <th>Locomotive Number</th>
                <th>Unit Address</th>
              </tr>
            </thead>
            <tbody>
              {Array.isArray(Records) && Records.map((record, index) => (
                <tr key={index} onClick={() => handleDetailClick(record.Data_type, record.id)}>
                  <td>{record.date_rec}</td>
                  <td>{record.symbol_id}</td>
                  <td>{record.locomotive_num}</td>
                  <td>{record.unit_addr}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Station;