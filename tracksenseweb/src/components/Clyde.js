import React from 'react';
import clyde from '../media/images/clyde.png';
import sign from '../media/images/clyde_sign_icon.png';
import Station from './Station'


const Clyde = () => {
  return (
    <Station station="Clyde" image={clyde} locationImage={sign} />
  );
};

export default Clyde;
