import React, { useState, useEffect } from 'react';
import config from '../config';
import './css/Options.css';

const Options = () => {
    const [stations, setStations] = useState([]);
    const [message, setMessage] = useState('');
    const [startTime, setStartTime] = useState('');
    const [endTime, setEndTime] = useState('');
    const timeStringRegex = /[0-9][0-9]:[0-9][0-9]/; // used for the way time is returned from the API
    const [newpushover, setNewPushover] = useState('');

    // Fetch user preferences
    useEffect(() => {
        const token = document.cookie
            .split('; ')
            .find((row) => row.startsWith('token='))
            ?.split('=')[1];

        fetch(`${config.apiUrl}/user_preferences`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error('Failed to fetch preferences');
                }
                return response.json();
                 // Parse the response JSON
            })
            .then((data) => {
                let start_str = timeStringRegex.exec(data[0].start_time)[0];
                let end_str = timeStringRegex.exec(data[0].end_time)[0];
                setStartTime(start_str);
                setEndTime(end_str);
                setStations(data); // Set the stations state with the fetched data
            })
            .catch((error) => {
                console.error('Error fetching preferences:', error);
            });
    }, []);

    // Handle station selection toggle
    const toggleStation = (stationId) => {
        setStations((prevStations) =>
            prevStations.map((station) =>
                station.station_id === stationId
                    ? { ...station, selected: !station.selected }
                    : station
            )
        );
    };

    // Save preferences
    const savePreferences = () => {
        const selectedStations = stations
            .filter((station) => station.selected)
            .map((station) => station.station_id);

        const token = document.cookie
            .split('; ')
            .find((row) => row.startsWith('token='))
            ?.split('=')[1];

        fetch(`${config.apiUrl}/user_preferences`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({ preferences: selectedStations }),
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error('Failed to save preferences');
                }
                return response.json(); // Parse the response JSON
            })
            .then((data) => {
                setMessage(data.message); // Display success message
            })
            .catch((error) => {
                console.error('Error saving preferences:', error);
                setMessage('Failed to save preferences'); // Display error message
            });
        fetch (`${config.apiUrl}/user_preferences/time`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({'starting_time': startTime, 'ending_time': endTime})
        })
        .then ((response) => {
            if (!response.ok) {
                throw new Error('Failed to save time settings.');
            }
        })
        .then((data) => {
            return;
        })
        .catch((error) => {
            console.error('Error Saving time settings: ', error)
        })
    };

    const update_pushover = () => {

        const new_id = newpushover
        const token = document.cookie
        .split('; ')
        .find((row) => row.startsWith('token='))
        ?.split('=')[1];

    fetch(`${config.apiUrl}/PushoverUpdater`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        }, body: JSON.stringify(
            {'pushover_id': newpushover})
        })
        .then((response) => {
            if(!response.ok){
                throw new Error("Failed to update Pushover Id");
            }
            return response.json();
        }
        
        ).then((data) => {
            setMessage(data.message); 
        }).catch((error) => {
            console.error('Error updating Pushover Id: ', error)
            setMessage("Failed to update Pushover Id");
        })
    }

    return (
        <div className="options-container">
            <h2>Notification Preferences</h2>
            {message && <p className="message">{message}</p>}
    
            <div className="pushover-section">
                <h3>Link Pushover Id</h3>
                <p>If you do not have a Pushover Id linked to your account or need to update it, please enter it below</p>
                <div>
                    <label>New Pushover Id: </label><br />
                    <input
                        type="text"
                        onChange={(e) => setNewPushover(e.target.value)}
                        placeholder="Enter new Pushover Id"
                        value={newpushover}
                    />
                    <button className="button-option" onClick={update_pushover}>Update Id</button>
                </div>
            </div>
    
            <div className="time-settings">
                <h3>Time Settings</h3>
                <p>Note: All times use Eastern time zones! (UTC-4/5 depending on the time of year)</p>
                <div className="time-input">
                    <label>Start time</label>
                    <input
                        type="text"
                        onChange={(e) => setStartTime(e.target.value)}
                        placeholder="00:00"
                        value={startTime}
                    />
                </div>
                <div className="time-input">
                    <label>End time</label>
                    <input
                        type="text"
                        onChange={(e) => setEndTime(e.target.value)}
                        placeholder="23:59"
                        value={endTime}
                    />
                </div>
            </div>
    
            <div className="station-list-container">
                <h3>Station Preferences</h3>
                <ul className="station-list">
                    {stations.map((station) => (
                        <li key={station.station_id}>
                            <label>
                                <input
                                    type="checkbox"
                                    checked={station.selected}
                                    onChange={() => toggleStation(station.station_id)}
                                />
                                {station.station_name}
                            </label>
                        </li>
                    ))}
                </ul>
            </div>
    
            <button className="button-option" onClick={savePreferences}>Save Preferences</button>
        </div>
    );
};

export default Options;