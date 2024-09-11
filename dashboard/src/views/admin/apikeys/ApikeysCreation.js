import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import {
  CButton,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CRow,
  CForm,
  CFormInput,
  CFormLabel,
  CFormFeedback,
  CAlert,
} from '@coreui/react'
import propTypes from 'prop-types'
import { createApiKey } from '../../../api'

const ApikeysCreation = ({ refreshApiKeys }) => {
  const [success, setSuccess] = useState(false)
  const [errorRequest, setErrorRequest] = useState(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm()

  const onSubmit = async (data) => {
    console.log('Form data:', data)
    if (data?.client.length < 6) {
      setError('client', {
        type: 'manual',
        message: 'Client name must be at least 6 characters long',
      })
      return
    }

    try {
      const response = await createApiKey(data.client, data.description)
      console.log({ response })
      setSuccess(response)
      refreshApiKeys()
    } catch (error) {
      console.error('Create API key failed:', error)
      setErrorRequest(error)
    }

    return
  }

  return (
    <CRow>
      <CCol xs={12}>
        <CCard className="mb-4">
          <CCardHeader>
            <strong>API Key</strong> <small>Create a new API key</small>
          </CCardHeader>
          <CCardBody>
            <p className="text-body-secondary small">Create a new API key</p>
            <CForm onSubmit={handleSubmit(onSubmit)}>
              <CRow className="mb-3">
                <CFormLabel htmlFor="client" className="col-sm-2 col-form-label">
                  Client
                </CFormLabel>
                <div className="col-sm-10">
                  <CFormInput
                    type="text"
                    id="client"
                    placeholder="Enter your client name"
                    {...register('client', {
                      required: 'Client name is required',
                      minLength: {
                        value: 6,
                        message: 'Client name must be at least 6 characters long',
                      },
                    })}
                    invalid={!!errors.client}
                  />

                  {errors.client && <CFormFeedback invalid>{errors.client.message}</CFormFeedback>}
                </div>
              </CRow>
              <CRow className="mb-3">
                <CFormLabel htmlFor="description" className="col-sm-2 col-form-label">
                  Description
                </CFormLabel>
                <div className="col-sm-10">
                  <CFormInput
                    type="text"
                    id="description"
                    placeholder="Enter your description"
                    // Register the field with validation
                    {...register('description', {
                      required: 'Description is required',
                      minLength: {
                        value: 6,
                        message: 'Description must be at least 6 characters long',
                      },
                    })}
                    invalid={!!errors.description}
                  />
                  {/* Display error message if any */}
                  {errors.description && (
                    <CFormFeedback invalid>{errors?.description?.message}</CFormFeedback>
                  )}
                </div>
              </CRow>
              <div className="text-center">
                <CButton color="success" type="submit" className="mb-3" disabled={isSubmitting}>
                  {isSubmitting ? 'Creating...' : 'Create API key'}
                </CButton>
              </div>
            </CForm>
            {success && (
              <CAlert color="success">
                Client: <strong>{success?.client}</strong> <br />
                Your API key is: <strong>{success?.apiKey}</strong>
              </CAlert>
            )}
            {errorRequest && (
              <CAlert color="danger">
                Error: <strong>{errorRequest.message}</strong>
              </CAlert>
            )}
          </CCardBody>
        </CCard>
      </CCol>
    </CRow>
  )
}

ApikeysCreation.propTypes = {
  refreshApiKeys: propTypes.func.isRequired,
}

export default ApikeysCreation
