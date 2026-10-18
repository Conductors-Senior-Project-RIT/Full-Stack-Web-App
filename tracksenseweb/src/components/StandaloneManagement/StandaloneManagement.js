import React from 'react';
import PropTypes from 'prop-types';
import styles from './StandaloneManagement.scss';

const StandaloneManagement = props => (
	<div>This is a component called StandaloneManagement.</div>
);

// todo: Unless you need to use lifecycle methods or local state,
// write your component in functional form as above and delete
// this section. 
// class StandaloneManagement extends React.Component {
//   render() {
//     return <div>This is a component called StandaloneManagement.</div>;
//   }
// }

const StandaloneManagementPropTypes = {
	// always use prop types!
};

StandaloneManagement.propTypes = StandaloneManagementPropTypes;

export default StandaloneManagement;
