import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import ReactPaginate from 'react-paginate';
import './css/Data.css';
import './css/Paginate.css';
import config from '../config';

const HotData = () => {
    const [data, setData] = useState([]); // Original data from the API
    const [filteredData, setFilteredData] = useState([]); // Data to display after filtering
    const [globalFilter, setGlobalFilter] = useState(''); // Single filter for all fields
    const [totalPages, setTotalPages] = useState(1);

    const [searchParams, setSearchParams] = useSearchParams();
    const page = parseInt(searchParams.get("page") || "1");

    useEffect(() => {
        // Fetch data from the record_collation API
        fetch(`${config.apiUrl}/record_collation?page=${page}&type=2`)
            .then(response => response.json())
            .then(data => {
                console.log('Fetched HOT data:', data); // Log the fetched data for debugging
                setData(data.results);
                setTotalPages(data.totalPages);
                setFilteredData(data.results); // Initialize filtered data
            })
            .catch(error => console.error('Error fetching HOT data:', error));
    }, [page]);

    // Handle filtering logic
    useEffect(() => {
        if (!globalFilter) {
            setFilteredData(data); // If no filter, show all data
            return;
        }

        const lowerCaseFilter = globalFilter.toLowerCase();

        const filtered = data.filter(item => {
            // Exact match fields
            const exactMatchFields = [
                item.signal_strength?.toLowerCase(),
                item.verified?.toLowerCase(),
                item.locomotive_num?.toLowerCase()
            ];

            // Partial match fields
            const partialMatchFields = [
                item.station_name?.toLowerCase(),
                item.date_rec?.toLowerCase(),
                item.unit_addr?.toLowerCase()
            ];

            // Check for exact matches
            const exactMatch = exactMatchFields.some(field => field === lowerCaseFilter);

            // Check for partial matches
            const partialMatch = partialMatchFields.some(field => field?.includes(lowerCaseFilter));

            return exactMatch || partialMatch;
        });

        setFilteredData(filtered);
    }, [globalFilter, data]);

    const handlePageClick = (event) => {
        const newPage = event.selected + 1;
        setSearchParams({ page: newPage });
    };

    return (
        <div className="data-table-container">
            <h2>HOT Records</h2>

            {/* Global Filter */}
            <div className="filter-container">
                <label htmlFor="globalFilter">Search:</label>
                <input
                    type="text"
                    id="globalFilter"
                    value={globalFilter}
                    onChange={(e) => setGlobalFilter(e.target.value)}
                    placeholder="Enter search term (e.g., Verified, 2025-04-04, Locomotive123)"
                />
            </div>

            {/* Data Table */}
            <table className="data-table">
                <thead>
                    <tr>
                        <th>Station Name</th>
                        <th>Start Time</th>
                        <th>Symbol</th>
                        <th>Unit Address</th>
                        <th>Signal Strength</th>
                        <th>Locomotive Number</th>
                        <th>Duration</th>
                        <th>End Time</th>
                    </tr>
                </thead>
                <tbody>
                    {filteredData.map((item, index) => (
                        <tr key={index}>
                            <td>{item.station_name}</td>
                            <td>{item.first_seen}</td>
                            <td>{item.symbol_name}</td>
                            <td>{item.unit_addr}</td>
                            <td>{item.signal_strength}</td>
                            <td>{item.locomotive_num}</td>
                            <td>{item.duration}</td>
                            <td>{item.last_seen}</td>
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
    );
};

export default HotData;