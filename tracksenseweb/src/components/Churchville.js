import React from 'react';
import churchville from '../media/images/churchville.png';
import sign from '../media/images/churchville_sign_icon.png';
import Station from './Station';


const Churchville = () => {
  return (
    <Station station="Churchville" image={churchville} locationImage={sign} />
  );
};

export default Churchville;