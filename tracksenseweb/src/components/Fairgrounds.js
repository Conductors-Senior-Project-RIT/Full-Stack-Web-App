import React from 'react';
import fairgrounds from '../media/images/fairgrounds.png';
import sign from '../media/images/fairgrounds_sign_icon.png';
import Station from './Station'


const Fairgrounds = () => {
  return (
    <Station station="Fairgrounds" image={fairgrounds} locationImage={sign} />
  );
};

export default Fairgrounds;