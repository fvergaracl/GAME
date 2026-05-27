import React from 'react'
import {
  CAvatar,
  CDropdown,
  CDropdownDivider,
  CDropdownHeader,
  CDropdownItem,
  CDropdownMenu,
  CDropdownToggle,
} from '@coreui/react'
import { cilAccountLogout, cilLockLocked, cilUser } from '@coreui/icons'
import CIcon from '@coreui/icons-react'

import avatar8 from './../../assets/images/avatars/2.jpg'
import keycloak from '../../keycloak'

const AppHeaderDropdown = () => {
  const authenticated = Boolean(keycloak.authenticated)
  const profile = keycloak.tokenParsed || {}
  const displayName =
    profile.preferred_username || profile.email || profile.name || 'Account'

  const handleLogin = () => {
    keycloak.login({ redirectUri: window.location.href })
  }
  const handleLogout = () => {
    keycloak.logout({ redirectUri: window.location.origin })
  }

  if (!authenticated) {
    return (
      <CDropdown variant="nav-item">
        <CDropdownToggle placement="bottom-end" className="py-0 pe-0" caret={false}>
          <CAvatar src={avatar8} size="md" />
        </CDropdownToggle>
        <CDropdownMenu className="pt-0" placement="bottom-end">
          <CDropdownHeader className="bg-body-secondary fw-semibold mb-2">
            Not signed in
          </CDropdownHeader>
          <CDropdownItem as="button" type="button" onClick={handleLogin}>
            <CIcon icon={cilLockLocked} className="me-2" />
            Log in with Keycloak
          </CDropdownItem>
        </CDropdownMenu>
      </CDropdown>
    )
  }

  return (
    <CDropdown variant="nav-item">
      <CDropdownToggle placement="bottom-end" className="py-0 pe-0" caret={false}>
        <CAvatar src={avatar8} size="md" />
      </CDropdownToggle>
      <CDropdownMenu className="pt-0" placement="bottom-end">
        <CDropdownHeader className="bg-body-secondary fw-semibold mb-2">
          {displayName}
        </CDropdownHeader>
        <CDropdownItem href="#">
          <CIcon icon={cilUser} className="me-2" />
          Profile
        </CDropdownItem>
        <CDropdownDivider />
        <CDropdownItem as="button" type="button" onClick={handleLogout}>
          <CIcon icon={cilAccountLogout} className="me-2" />
          Log out
        </CDropdownItem>
      </CDropdownMenu>
    </CDropdown>
  )
}

export default AppHeaderDropdown
