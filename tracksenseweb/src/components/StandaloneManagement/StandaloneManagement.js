import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import styles from './StandaloneManagement.scss';
import config from '../../config';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';

const StandaloneManagement = props => {
	const [addData, setAddData] = useState(null);
	const [getData, setGetData] = useState([]);
	const [getName, setName] = useState(null);
	const [getIdToRemove, setIdToRemove] = useState('');
	const [getPasswordId, setPasswordId] = useState('');
	const [passwd, setPasswd] = useState(null)

	function getCsrfToken() {
		const value = `; ${document.cookie}`;
		const parts = value.split(`; csrf_access_token=`);
		if (parts.length === 2) return parts.pop().split(';').shift();
	}

	//TODO: Add coordinates to this. Will also need to add to API

	const handleStandaloneAdd = async (e) => {
		e.preventDefault();

		try {
			const response = await fetch(`${config.apiUrl}/station_auth`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					"X-CSRF-TOKEN": getCsrfToken(),
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
					"X-CSRF-TOKEN": getCsrfToken(),
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

	const handlePasswdGet = async (e) => {
		var result;

		try {
			const response = await fetch(`${config.apiUrl}/station_passwd?id=${getPasswordId}`, {
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
					"X-CSRF-TOKEN": getCsrfToken(),
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

		setPasswd(result.password);
	};

	const handleStandaloneRemove = async (e) => {
		e.preventDefault();

		try {
			const response = await fetch(`${config.apiUrl}/station_auth?id=${getIdToRemove}`, {
				method: 'DELETE',
				headers: {
					'Content-Type': 'application/json',
					"X-CSRF-TOKEN": getCsrfToken(),
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

	const handleSetPasswordId = async (id) => {
		setPasswordId(id);
	}

	useEffect(() => {
		handleStandaloneGet();
	}, []);

	return (
		<div className="container">
			<section>
				<h2>Add Standalone</h2>
				<Form onSubmit={handleStandaloneAdd}>
					<label>
						New Standalone Name:
						<input
							type="text"
							placeholder="Enter name of station"
							value={getName ?? ''}
							onChange={e => setName(e.target.value)}
						/>
					</label>
					<button type='submit'>Add Standalone</button>
					{addData && <p>Station password: <code>{addData.password}</code></p>}
				</Form>
			</section>

			<section>
				<h2>Get Standalone Password</h2>
				<label>
					<Row>
						<Col>Select Standalone:</Col>
					</Row>
					<Row>
						<Col sm={9}>
							<Form.Select value={getPasswordId} onChange={e => handleSetPasswordId(e.target.value)}>
								{getData.map((standalone) => (
									<option key={standalone.station_name} value={standalone.id}>
										{standalone.station_name}
									</option>
								))}
							</Form.Select>
						</Col>
						<Col sm={3}>
							<button onClick={handlePasswdGet}>Get</button>
						</Col>
					</Row>
					<Row>
						{passwd && <p>Station password: <code>{passwd}</code></p>}
					</Row>
				</label>
			</section>

			<section>
				<h2>Remove Standalone</h2>
				<label>
					<Row>
						<Col>Select Standalone:</Col>
					</Row>
					<Row>
						<Col sm={9}>
							<Form.Select value={getIdToRemove} onChange={e => handleSetIdToDelete(e.target.value)}>
								{getData.map((standalone) => (
									<option key={standalone.station_name} value={standalone.id}>
										{standalone.station_name}
									</option>
								))}
							</Form.Select>
						</Col>
						<Col sm={3}>
							<button className='red-button' onClick={handleStandaloneRemove}>Remove</button>
						</Col>
					</Row>
				</label>
			</section>
		</div>
	);
};

const StandaloneManagementPropTypes = {
	// always use prop types!
};

StandaloneManagement.propTypes = StandaloneManagementPropTypes;

export default StandaloneManagement;
