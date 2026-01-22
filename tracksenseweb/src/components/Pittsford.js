import React from 'react';
import pittsford from '../media/images/pittsford.png';
import sign from '../media/images/pittsford_sign_icon.png';
import Station from './Station'


const Pittsford = () => {
  return (
    <Station station="Pittsford" image={pittsford} locationImage={sign} />
  );
};

export default Pittsford;