import React, { useState, useEffect } from 'react';
import './css/Verification.css';
import config from '../config';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import { Typeahead } from 'react-bootstrap-typeahead';
import 'react-bootstrap-typeahead/css/Typeahead.css';
import ReactPaginate from 'react-paginate';
import './css/Paginate.css';
import { useSearchParams } from 'react-router-dom';

const VerifyHOT = () => {
  // Data state
  const [data, setData] = useState([]);
  const [symbols, setSymbols] = useState([]);
  const [totalPages, setTotalPages] = useState(1);

  // Modal state
  const [show, setShow] = useState(false);
  const [modalId, setModalId] = useState(null);
  const [modalUnitAddr, setModalUnitAddr] = useState(null);
  const [modalSymbol, setModalSymbol] = useState(null);
  const [modalEngineNum, setModalEngineNum] = useState(null);

  const [searchParams, setSearchParams] = useSearchParams();
  const page = parseInt(searchParams.get("page") || "1");

  // Fetch data from the API
  useEffect(() => {
    fetch(`${config.apiUrl}/verifier_hot?page=${page}`)
      .then(response => response.json())
      .then(data => {
        setData(data.results);
        setTotalPages(data.totalPages);
      })
      .catch(error => console.error('Error fetching HOT data:', error));

    fetch(`${config.apiUrl}/symbols`)
      .then(response => response.json())
      .then(symbols => setSymbols(symbols))
      .catch(error => console.error('Error fetching symbols:', error));
  }, [page]);

  // Perform verification
  const performVerification = () => {
    let symbolId = -1;
    fetch(`${config.apiUrl}/symbol_ids?symbol_name=${modalSymbol}`)
      .then(response => response.json())
      .then(data => {
        symbolId = data.id;
        if (symbolId !== -1) {
          fetch(`${config.apiUrl}/verifier_hot`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              id: modalId,
              symbol: symbolId,
              engine_number: modalEngineNum,
            }),
          })
            .then(response => response.ok)
            .then(response => {
              if (response) {
                console.log('HOT record verified successfully.');
                window.location.reload(); // Reload the page
              }
            });
        }
      });
  };

  // Handle modal show
  const handleShow = (item) => {
    setModalId(item.id);
    setModalUnitAddr(item.unit_addr);
    setModalSymbol(item.symbol);
    setModalEngineNum(item.locomotive_num);
    setShow(true);
  };

  // Handle modal close
  const handleClose = () => setShow(false);

  // Handle verification
  const handleVerify = () => {
    handleClose();
    if (symbols.includes(modalSymbol)) {
      performVerification();
    } else {
      // Add new symbol and then verify
      fetch(`${config.apiUrl}/symbols`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: modalSymbol,
        }),
      })
        .then(response => response.ok)
        .then(response => {
          if (response) performVerification();
        });
    }
  };

  // Handle pagination
  const handlePageClick = (event) => {
    const newPage = event.selected + 1;
    setSearchParams({ page: newPage });
  };

  return (
    <div>
      <Modal
        show={show}
        onHide={handleClose}
        backdrop="static"
        keyboard={false}
        dialogClassName="modal-top"
      >
        <Modal.Header closeButton>
          <Modal.Title>Verify HOT Data</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group>
              <Form.Label>Unit Address</Form.Label>
              <Form.Control
                type="text"
                value={modalUnitAddr}
                onChange={(e) => setModalUnitAddr(e.target.value)}
              />
            </Form.Group>
            <Form.Group>
              <Form.Label>Symbol</Form.Label>
              <Typeahead options={symbols} onInputChange={(e) => {setModalSymbol(e.target.value);}} onChange={(val) => { setModalSymbol(val[0]);}} value={modalSymbol}/>
            </Form.Group>
            <Form.Group>
              <Form.Label>Engine Number</Form.Label>
              <Form.Control
                type="text"
                value={modalEngineNum}
                onChange={(e) => setModalEngineNum(e.target.value)}
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleClose}>
            Close
          </Button>
          <Button className="verify-button" variant="primary" onClick={handleVerify}>
            Verify
          </Button>
        </Modal.Footer>
      </Modal>
      <div className="data-table-container">
        <h2>Unverified HOT Data</h2>
        <table className="data-table">
          <thead>
            <tr>
              <th>Station Name</th>
              <th>Timestamp</th>
              <th>Unit Address</th>
              <th>Locomotive Number</th>
              <th>Signal Strength</th>
              <th>Verified</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item, index) => (
              <tr key={index}>
                <td>{item.station_name}</td>
                <td>{item.date_rec}</td>
                <td>{item.unit_addr}</td>
                <td>{item.locomotive_num}</td>
                <td>{item.signal_strength}</td>
                <td>{item.verified ? 'Yes' : 'No'}</td>
                <td>
                  <button onClick={() => handleShow(item)}>Verify</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <ReactPaginate
          pageCount={totalPages}
          containerClassName="pagination"
          onPageChange={handlePageClick}
          forcePage={page - 1}
        />
      </div>
    </div>
  );
};

export default VerifyHOT;