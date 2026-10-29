import React from 'react';
import { shallow, render, mount } from 'enzyme';
import StandaloneManagement from './StandaloneManagement';

describe('StandaloneManagement', () => {
  let props;
  let shallowStandaloneManagement;
  let renderedStandaloneManagement;
  let mountedStandaloneManagement;

  const shallowTestComponent = () => {
    if (!shallowStandaloneManagement) {
      shallowStandaloneManagement = shallow(<StandaloneManagement {...props} />);
    }
    return shallowStandaloneManagement;
  };

  const renderTestComponent = () => {
    if (!renderedStandaloneManagement) {
      renderedStandaloneManagement = render(<StandaloneManagement {...props} />);
    }
    return renderedStandaloneManagement;
  };

  const mountTestComponent = () => {
    if (!mountedStandaloneManagement) {
      mountedStandaloneManagement = mount(<StandaloneManagement {...props} />);
    }
    return mountedStandaloneManagement;
  };  

  beforeEach(() => {
    props = {};
    shallowStandaloneManagement = undefined;
    renderedStandaloneManagement = undefined;
    mountedStandaloneManagement = undefined;
  });

  // Shallow / unit tests begin here
 
  // Render / mount / integration tests begin here
  
});
