import React from 'react';
import fairport from '../media/images/fairport.png';
import sign from '../media/images/fairport_sign_icon.png';
import Station from './Station'


const Fairport = () => {
  return (
    <Station station="Fairport" image={fairport} locationImage={sign} />
  );
};

export default Fairport;