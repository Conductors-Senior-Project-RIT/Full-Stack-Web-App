import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import styles from './StandaloneManagement.scss';
import config from '../../config';

const StandaloneManagement = props => {
	const [addData, setAddData] = useState(null);
	const [getData, setGetData] = useState([]);
	const [getName, setName] = useState(null);
	const [getIdToRemove, setIdToRemove] = useState('');

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
				body: JSON.stringify({ station_name: getName }),
			});
			const result = await response.json();

			if (!response.ok) {
				console.error('Error:', result.error);
			}

			setAddData(result)

			await handleStandaloneGet();

		} catch (error) {
			console.error('Error:', error);
		}
	};

	const handleStandaloneGet = async (e) => {
		var result;

		try {
			const response = await fetch(`${config.apiUrl}/station_auth`, {
				method: 'GET',
				headers: {
				'Content-Type': 'application/json',
				},
				credentials: "include",
			});
			result = await response.json();

			if (!response.ok) {
				console.error('Error:', result.error);
			}

		} catch (error) {
			console.error('Error:', error);
		}

		const sorted = [...result].sort((a, b) =>
			a.station_name.localeCompare(b.station_name)
		)
		setGetData(sorted);
	};

	const handleStandaloneRemove = async (e) => {
		e.preventDefault();

		try {
			const response = await fetch(`${config.apiUrl}/station_auth?id=${getIdToRemove}`, {
				method: 'DELETE',
				headers: {
				'Content-Type': 'application/json',
				},
				credentials: "include",
			});
			const result = await response.json();

			if (!response.ok) {
				console.error('Error:', result.error);
			}
		
			await handleStandaloneGet();

		} catch (error) {
			console.error('Error:', error);
		}
	};

	const handleSetIdToDelete = async (id) => {
		setIdToRemove(id);
	}

	useEffect(() => {
		handleStandaloneGet();
	}, []);

	return (
		<div>
			<h2>Add Standalone</h2>
			<input
				type="text"
				placeholder="Enter name of station"
				value={getName ?? ''}
				onChange={e => setName(e.target.value)}
			/>
			<button onClick={handleStandaloneAdd}>Add Standalone</button>
			{addData && <p>Station password: <code>{addData.password}</code></p>}
			<h2>Remove Standalone</h2>
			<select value={getIdToRemove} onChange={e => handleSetIdToDelete(e.target.value)}>
				{getData.map((standalone) => (
					<option key={standalone.station_name} value={standalone.id}>
						{standalone.station_name}
					</option>
				))}
			</select>
			<button onClick={handleStandaloneRemove}>Remove Standalone</button>
		</div>
	);
};

const StandaloneManagementPropTypes = {
	// always use prop types!
};

StandaloneManagement.propTypes = StandaloneManagementPropTypes;

export default StandaloneManagement;
