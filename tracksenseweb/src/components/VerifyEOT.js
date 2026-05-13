import React, { useState, useEffect } from 'react';
import './css/Verification.css';
import config from '../config';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button'
import Form from 'react-bootstrap/Form';
import { Typeahead } from 'react-bootstrap-typeahead';
import 'react-bootstrap-typeahead/css/Typeahead.css';
import ReactPaginate from 'react-paginate';
import './css/Paginate.css'
import { useSearchParams } from 'react-router-dom';

function getCsrfToken() {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; csrf_access_token=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

const VerifyEOT = () => {
  //data
  const [data, setData] = useState([]);
  const [symbols, setSymbols] = useState([])
  //whether or not the modal is active
  const [show, setShow] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();
  const page = parseInt(searchParams.get("page") || "1");
  const [totalPages, setTotalPages] = useState(1);

  //modal information state
  const [modalId, setModalId] = useState(null);
  const [modalUnitAddr, setModalUnitAddr] = useState(null);
  const [modalSymbol, setModalSymbol] = useState(null);
  const [modalItem, setModalItem] = useState(null);
  const [modalIndex, setModalIndex] = useState(null);
  const [modalLocomotiveNum, setModalLocomotiveNum] = useState(null);

  const performVerification = async () => {
    //first get the symbol id
    let symbolId = -1;

    try{
      const symbolResponse = await fetch(`${config.apiUrl}/symbols?symbol_name=${modalSymbol}`);
      const symbolData = await symbolResponse.json();
      symbolId = symbolData.id;

      if (symbolId !== -1) {
        console.log("symbolID: " + symbolId);
        console.log("modalID: " + modalId);
        const verifyResponse = await fetch(`${config.apiUrl}/record_verifier`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-TOKEN": getCsrfToken(),
          },
          credentials: "include",
          body: JSON.stringify({
            "id": modalId,
            "symbol": symbolId,
            "engine_number": modalLocomotiveNum
          })
        });
        if (verifyResponse.ok) {
          console.log("verified information sent, verifying data");
          window.location.reload();
        }
      }
    }catch(error){
      console.error('error with verification:', error);
    }
  };

  const handleShow = (item, index) => {
    // get important information from the eot record
    //this is not final, and will probably change once ken sees it
    let record_id = item.id;
    let symbol = item.symbol;
    let unit_addr = item.unit_addr;
    setModalItem(item);
    setModalSymbol(symbol)
    setModalUnitAddr(unit_addr);
    setModalId(record_id);
    setShow(true);
  };

  const handleClose = () => setShow(false);

  const handleVerify = async () => {
    handleClose();
    if (symbols.includes(modalSymbol)) {
      performVerification();
    }
    else {
      try {
        // api call to add symbol
        const response = await fetch(`${config.apiUrl}/symbols`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            // "X-CSRF-TOKEN": getCsrfToken(), // this endpoint doesnt have @role_required() (@jwt_required but extra functionality); commented out for now
          },
          body: JSON.stringify({ 'name': modalSymbol })
        });
        if (response.ok) performVerification();
      } catch (error) {
        console.error('Error adding symbol:', error);
      }
      //api call to verify with symbol ID
    }
  };

  const handlePageClick = (event) => {
    const newPage = event.selected + 1;
    setSearchParams({page: newPage});
  }

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${config.apiUrl}/record_verifier?page=${page}&type=1`, {
          method: "GET",
          credentials: "include",
        });
        const result = await response.json();
        setData(result.results);
        setTotalPages(result.totalPages);
      } catch (error) {
        console.error('Error fetching data:', error);
      }

      try{
        const symbolResponse = await fetch(`${config.apiUrl}/symbols`);
        const symbolData = await symbolResponse.json();
        if (symbolData && symbolData.results) {
          setSymbols(symbolData.results);
        } else {
          console.error('Response payload empty!');
        }
      } catch (error) {
        console.error("A problem has occurred: ", error);
      }
    };
    fetchData();
  }, [page]);

    return (
      <div>
        <Modal
        show={show}
        onHide={handleClose}
        backdrop="static"
        keyboard={false}
        dialogClassName="modal-top" // Custom class to position the modal at the top
      >
        <Modal.Header closeButton>
            <Modal.Title>Verify Data</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form>
              <Form.Group>
                <Form.Label>
                  Unit Address
                </Form.Label>
                <Form.Control type="text" value={modalUnitAddr} onChange={(e) => {setModalUnitAddr(e.target.value);}} />
              </Form.Group>
              <Form.Group>
                <Form.Label>
                  Symbol
                </Form.Label>
                {/* <Form.Control type="text" placeholder={modalSymbol} onChange={(e) => {setModalSymbol(e); console.log(modalSymbol);}}/> */}
                <Typeahead options={symbols} onInputChange={(e) => {setModalSymbol(e.target.value);}} onChange={(val) => { setModalSymbol(val[0]);}} value={modalSymbol}/>
              </Form.Group>
              <Form.Group>
                <Form.Label>Locomotive Number</Form.Label>
                <Form.Control type="text" value={modalLocomotiveNum} onChange={(e) => {setModalLocomotiveNum(e.target.value)}}/>
              </Form.Group>
            </Form>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={handleClose}>Close</Button>
            <Button className="verify-button" variant="primary" onClick={handleVerify}>Verify</Button>
          </Modal.Footer>
        </Modal>
        <div className="data-table-container">
          <h2>Unverified EOT Data</h2>
          <table className="data-table">
          <thead>
                      <tr>
                          <th>Location</th>
                          <th>Timestamp</th>
                          <th>Unit Address</th>
                          <th>Pressure</th>
                          <th>Motion</th>
                          <th>Marker Light</th>
                          <th>Turbine</th>
                          <th>Battery Cond.</th>
                          <th>Battery Charge</th>
                          <th>Arm Status</th>
                      </tr>
                  </thead>
                  <tbody>
                      {data.map((item, index) => (
                          <tr key={index}>
                              <td>{item.station_name}</td>
                              <td>{item.date_rec}</td>
                              <td>{item.unit_addr}</td>
                              <td>{item.brake_pressure}</td>
                              <td>{item.motion}</td>
                              <td>{item.marker_light}</td>
                              <td>{item.turbine}</td>
                              <td>{item.battery_cond}</td>
                              <td>{item.battery_charge}</td>
                              <td>{item.arm_status}</td>
                              <td><button onClick={() => handleShow(item, index)}>Verify</button></td>
                          </tr>
                      ))}
                  </tbody>
          </table>
          <ReactPaginate 
                    pageCount={totalPages}
                    containerClassName='pagination'
                    onPageChange={handlePageClick}
                    forcePage={page-1}
                    />
        </div>
      </div>
      
      
    )

};

export default VerifyEOT;