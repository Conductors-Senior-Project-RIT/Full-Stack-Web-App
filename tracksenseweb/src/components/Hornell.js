import React from 'react';
import hornell from '../media/images/hornell.png';
import sign from '../media/images/hornell_sign_icon.png';
import Station from './Station'


const Hornell = () => {
  return (
    <Station station="Hornell" image={hornell} locationImage={sign} />
  );
};

export default Hornell;