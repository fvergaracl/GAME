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
    console.log('authenticated', keycloak.authenticated)
    const token = keycloak.token
    console.log(token)
    if (token) {
      const payload = token.split('.')[1]
      const decoded_payload = JSON.parse(atob(payload))
      if (decoded_payload?.resource_access?.account?.roles?.includes('AdministratorGAME')) {
        dispatch({ type: 'set', sidebarNav: _nav_administrator })
      } else {
        dispatch({ type: 'set', sidebarNav: _nav })
      }
    }
  }, [])

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
