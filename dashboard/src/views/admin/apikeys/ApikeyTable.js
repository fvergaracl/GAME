import React, { useEffect, useState } from 'react'
import {
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CRow,
  CTable,
  CTableBody,
  CTableHead,
  CTableHeaderCell,
  CTableRow,
  CTableDataCell,
  CPagination,
  CPaginationItem,
  CButton,
} from '@coreui/react'

// '@coreui/icons'
import { cilMagnifyingGlass, cilPencil, cilTrash } from '@coreui/icons'
import CIcon from '@coreui/icons-react'
// propTypes
import propTypes from 'prop-types'

const ApiKeyTable = ({ apiKeys }) => {
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 10

  // Calculate total number of pages
  const totalPages = Math.ceil(apiKeys.length / itemsPerPage)

  // Get current page data
  const currentApiKeys = apiKeys.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)

  const handlePageChange = (pageNumber) => {
    setCurrentPage(pageNumber)
  }

  return (
    <CRow>
      <CCol xs={12}>
        <CCard className="mb-4">
          <CCardHeader>
            <strong>API Key</strong> <small>Table of API keys</small>
          </CCardHeader>
          <CCardBody>
            <p className="text-body-secondary small">
              Table of API keys, you can manage them here.
            </p>

            <CTable striped>
              <CTableHead>
                <CTableRow>
                  <CTableHeaderCell scope="col">#</CTableHeaderCell>
                  <CTableHeaderCell scope="col">API Key</CTableHeaderCell>
                  <CTableHeaderCell scope="col">Client</CTableHeaderCell>
                  <CTableHeaderCell scope="col">Description</CTableHeaderCell>
                  <CTableHeaderCell scope="col">Created At</CTableHeaderCell>
                  <CTableHeaderCell scope="col">Actions</CTableHeaderCell>
                </CTableRow>
              </CTableHead>
              <CTableBody>
                {currentApiKeys.map((apiKey, index) => (
                  <CTableRow key={apiKey.apiKey}>
                    <CTableHeaderCell scope="row">
                      {(currentPage - 1) * itemsPerPage + index + 1}
                    </CTableHeaderCell>
                    <CTableDataCell>{apiKey.apiKey}</CTableDataCell>
                    <CTableDataCell>
                      <div className="text-truncate" style={{ maxWidth: '150px' }}>
                        {apiKey.client}
                      </div>
                    </CTableDataCell>
                    <CTableDataCell>
                      <div className="text-truncate" style={{ maxWidth: '150px' }}>
                        {apiKey.description}
                      </div>
                    </CTableDataCell>
                    <CTableDataCell>{new Date(apiKey.created_at).toLocaleString()}</CTableDataCell>
                    <CTableDataCell>
                      {/*
                            view , edit, delete buttons with icons
                            */}

                      <CButton color="primary" size="sm" className="me-2">
                        <CIcon icon={cilMagnifyingGlass} />
                      </CButton>
                      <CButton color="warning" size="sm" className="me-2">
                        <CIcon icon={cilPencil} />
                      </CButton>
                      <CButton color="danger" size="sm">
                        <CIcon icon={cilTrash} />
                      </CButton>
                    </CTableDataCell>
                  </CTableRow>
                ))}
              </CTableBody>
            </CTable>

            {/* Pagination */}
            <CPagination className="mt-4">
              <CPaginationItem
                disabled={currentPage === 1}
                onClick={() => handlePageChange(currentPage - 1)}
              >
                Previous
              </CPaginationItem>
              {[...Array(totalPages)].map((_, index) => (
                <CPaginationItem
                  key={index + 1}
                  active={index + 1 === currentPage}
                  onClick={() => handlePageChange(index + 1)}
                >
                  {index + 1}
                </CPaginationItem>
              ))}
              <CPaginationItem
                disabled={currentPage === totalPages}
                onClick={() => handlePageChange(currentPage + 1)}
              >
                Next
              </CPaginationItem>
            </CPagination>
          </CCardBody>
        </CCard>
      </CCol>
    </CRow>
  )
}

ApiKeyTable.propTypes = {
  apiKeys: propTypes.array.isRequired,
}

export default ApiKeyTable
