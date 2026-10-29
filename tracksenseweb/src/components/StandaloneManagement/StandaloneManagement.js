import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import styles from './StandaloneManagement.scss';
import config from '../../config';

const StandaloneManagement = props => {
	const [data, setData] = useState(null);
	const [name, setName] = useState(null);

	//TODO: Add coordinates to this. Will also need to add to API

	const handleStandaloneAdd = async (e) => {
			e.preventDefault();

			try {
				const response = await fetch(`${config.apiUrl}/station_auth`, {
					method: 'POST',
					headers: {
					'Content-Type': 'application/json',
					},
					credentials: "include",
					body: JSON.stringify({ station_name: name }),
				});
				const result = await response.json();
				console.log('Response data:', result);

				if (!response.ok) {
					console.error('Error:', result.error);
				}

				setData(result)

			} catch (error) {
				console.error('Error:', error);
			}
		};

	return (
		<div>
			<input
				type="text"
				placeholder="Enter name of station"
				value={name ?? ''}
				onChange={e => setName(e.target.value)}
			/>
			<button onClick={handleStandaloneAdd}>Add Test Standalone</button>
			{data && <p>Station password: <code>{data.password}</code></p>}
		</div>
	);
};

const StandaloneManagementPropTypes = {
	// always use prop types!
};

StandaloneManagement.propTypes = StandaloneManagementPropTypes;

export default StandaloneManagement;
