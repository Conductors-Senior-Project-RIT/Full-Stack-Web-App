import React, { useState, useEffect } from 'react';
import './css/Data.css';

const Data = () => {
    const [data, setData] = useState([]);

    useEffect(() => {
        // Fetch data from the API endpoint
        // Replace 'API_ENDPOINT' with the actual endpoint
        fetch('http://127.0.0.1:5000/history')
            .then(response => response.json())
            .then(data => setData(data))
            .catch(error => console.error('Error fetching data:', error));
    }, []);

    return (
        <div className="data-table-container">
            <h2>Historical Data</h2>
            <table className="data-table">
                <thead>
                    <tr>
                        <th>Unit Address</th>
                        <th>Pressure</th>
                        <th>Motion</th>
                        <th>Marker Light</th>
                        <th>Turbine</th>
                        <th>Battery Cond.</th>
                        <th>Battery Charge</th>
                        <th>Arm Status</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map((item, index) => (
                        <tr key={index}>
                            <td>{item.unit_addr}</td>
                            <td>{item.brake_pressure}</td>
                            <td>{item.motion}</td>
                            <td>{item.marker_light}</td>
                            <td>{item.turbine}</td>
                            <td>{item.battery_cond}</td>
                            <td>{item.battery_charge}</td>
                            <td>{item.arm_status}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default Data;