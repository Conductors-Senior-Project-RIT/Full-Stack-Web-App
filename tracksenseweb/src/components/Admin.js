import React, { useState, useEffect } from 'react';
import './css/Admin.css';
import config from '../config';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button'
import Form from 'react-bootstrap/Form';
import { Typeahead } from 'react-bootstrap-typeahead';
import 'react-bootstrap-typeahead/css/Typeahead.css';
import ReactPaginate from 'react-paginate';
import './css/Paginate.css'
import { useSearchParams } from 'react-router-dom';

const Admin = () => {
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

  const performVerification = () => {
    //first get the symbol id
    let symbolId = -1;
    fetch(`${config.apiUrl}/symbol_ids?symbol_name=${modalSymbol}`)
    .then(response => {
      return response.json()
    })
    .then(data => {
      // ensure we get a proper return - in theory this will always give a proper return
      // TODO: add error handling here
      symbolId = data.id
      if (symbolId != -1) {
        console.log("symbolID: " + symbolId);
        console.log("modalID: " + modalId);
        fetch(
          `${config.apiUrl}/record_verifier`, {
            method:"PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
              "id": modalId,
              "type": 1,
              "symbol": symbolId,
              "engine_number": modalLocomotiveNum
            })
          }
        )
        // using .then() in this manner forces the above fetch to finish before the rest of this is executed.
        .then(response => response.ok)
        .then (response => {
          if (response) {
            console.log("verified information sent, verifying data");
            window.location.reload() //reload the page
          }
        })
      }
    })
  }


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
  const handleVerify = () => {
    handleClose();
    if (symbols.includes(modalSymbol)) {
      performVerification();
    }
    else {
      // api call to add symbol
      fetch (`${config.apiUrl}/symbols`, {
        method:"POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          'name': modalSymbol
        })
      })
      .then(
        // doing this response check forces the first fetch to actually complete before execurting the rest of the code
        response => response.ok
      )
      .then(
        response => {
          if (response)
            performVerification()
        })
      
      //api call to verify with symbol ID
    }
  };

  const handlePageClick = (event) => {
    const newPage = event.selected + 1;
    setSearchParams({page: newPage});
  }

  useEffect(() => {
    fetch(`${config.apiUrl}/record_verifier?page=${page}&type=1`)
    .then(response => response.json())
    .then(data => {
      setData(data.results);
      setTotalPages(data.totalPages);
    })
    .catch(error => console.error('Error fetching data:', error));
    fetch(`${config.apiUrl}/symbols`)
    .then(response => response.json())
    .then(symbols => setSymbols(symbols))
    .catch(error => console.error("A problem has occurred: ", error))
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
            <Button variant="secondary" onClick={handleClose}>
              Close
            </Button>
            <Button className="button-admin" variant="primary" onClick={handleVerify}>Verify</Button>
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

export default Admin;