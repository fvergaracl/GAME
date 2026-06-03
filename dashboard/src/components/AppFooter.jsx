import React from 'react'
import { CFooter } from '@coreui/react'
import CIcon from '@coreui/icons-react'
import { cilExternalLink } from '@coreui/icons'

const AppFooter = () => {
  return (
    <CFooter className="px-4">
      <div>
        <a href="#" target="_blank" rel="noopener noreferrer">
          GAME
        </a>
        <span className="ms-1">&copy; 2023 - {new Date().getFullYear()} Dashboard.</span>
      </div>
      <div className="ms-auto">
        <span className="me-1">
          Source available
          <CIcon icon={cilExternalLink} size="sm" />
        </span>
        <a href="https://github.com/fvergaracl/GAME" target="_blank" rel="noopener noreferrer">
          https://github.com/fvergaracl/GAME
        </a>
      </div>
    </CFooter>
  )
}

export default React.memo(AppFooter)
