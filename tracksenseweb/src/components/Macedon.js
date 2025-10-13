import React from 'react';
import macedon from '../media/images/macedon.png';
import sign from '../media/images/macedon_sign_icon.png';
import Station from './Station'


const Macedon = () => {
  return (
    <Station station="Macedon" image={macedon} locationImage={sign} />
  );
};

export default Macedon;