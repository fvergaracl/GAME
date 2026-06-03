import React, { useEffect } from 'react'
import { useSelector, useDispatch } from 'react-redux'

import {
  CCloseButton,
  CSidebar,
  CSidebarBrand,
  CSidebarFooter,
  CSidebarHeader,
  CSidebarToggler,
} from '@coreui/react'
import CIcon from '@coreui/icons-react'

import { AppSidebarNav } from './AppSidebarNav'
import keycloak from '../keycloak'
import { logo } from 'src/assets/brand/logo'

// sidebar nav config
import { _nav, _nav_administrator } from '../_nav'

const AppSidebar = () => {
  const dispatch = useDispatch()
  const unfoldable = useSelector((state) => state.sidebarUnfoldable)
  const sidebarShow = useSelector((state) => state.sidebarShow)
  const sidebarNav = useSelector((state) => state.sidebarNav) || _nav
  useEffect(() => {
    // AdministratorGAME is a CLIENT role on the *backend* client
    // (VITE_KEYCLOAK_API_CLIENT_ID, e.g. game-backend), not on the public
    // SPA client used for the login flow (VITE_KEYCLOAK_CLIENT_ID,
    // e.g. game-frontend). The default "client roles" mapper in
    // Keycloak's roles scope aggregates roles across clients into
    // resource_access[<client>].roles regardless of which client
    // requested the token, so the lookup below resolves even when the
    // user logged in via the public SPA client.
    const apiClientId =
      import.meta.env.VITE_KEYCLOAK_API_CLIENT_ID ||
      import.meta.env.VITE_KEYCLOAK_CLIENT_ID
    const roles =
      keycloak.tokenParsed?.resource_access?.[apiClientId]?.roles ?? []
    if (roles.includes('AdministratorGAME')) {
      dispatch({ type: 'set', sidebarNav: _nav_administrator })
    } else {
      dispatch({ type: 'set', sidebarNav: _nav })
    }
  }, [keycloak.authenticated])

  return (
    <CSidebar
      className="border-end"
      colorScheme="dark"
      position="fixed"
      unfoldable={unfoldable}
      visible={sidebarShow}
      onVisibleChange={(visible) => {
        dispatch({ type: 'set', sidebarShow: visible })
      }}
    >
      <CSidebarHeader className="border-bottom">
        <CSidebarBrand to="/">
          <CIcon customClassName="sidebar-brand-full" icon={logo} height={32} />
          <CIcon customClassName="sidebar-brand-narrow" icon={logo} height={32} />
        </CSidebarBrand>
        <CCloseButton
          className="d-lg-none"
          dark
          onClick={() => dispatch({ type: 'set', sidebarShow: false })}
        />
      </CSidebarHeader>
      <AppSidebarNav items={sidebarNav} />
      <CSidebarFooter className="border-top d-none d-lg-flex">
        <CSidebarToggler
          onClick={() => dispatch({ type: 'set', sidebarUnfoldable: !unfoldable })}
        />
      </CSidebarFooter>
    </CSidebar>
  )
}

export default React.memo(AppSidebar)
