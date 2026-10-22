import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import styles from './StandaloneManagement.scss';
import config from '../../config';

const StandaloneManagement = props => {
	//TODO: Add coordinates to this. Will also need to add to API

	const handleStandaloneAdd = async (e) => {
			e.preventDefault();

			const station = "Test Station";
			try {
				const response = await fetch(`${config.apiUrl}/station_auth`, {
					method: 'POST',
					headers: {
					'Content-Type': 'application/json',
					},
					credentials: "include",
					body: JSON.stringify({ station_name: station }),
				});
				const data = await response.json();
				console.log('Response data:', data);

				if (!response.ok) {
					console.error('Error:', data.error);
				}
			} catch (error) {
				console.error('Error:', error);
			}
		};

	useEffect(() => {}, []);

	return (
		<div>
			This is a component called StandaloneManagement.
			<button onClick={handleStandaloneAdd}>Add Test Standalone</button>
		</div>
	);
};

const StandaloneManagementPropTypes = {
	// always use prop types!
};

StandaloneManagement.propTypes = StandaloneManagementPropTypes;

export default StandaloneManagement;
