import React from 'react'
import CIcon from '@coreui/icons-react'
import {
  cilBell,
  cilCalculator,
  cilChartPie,
  cilCursor,
  cilDescription,
  cilDrop,
  cilNotes,
  cilPencil,
  cilPuzzle,
  cilSpeedometer,
  cilStar,
} from '@coreui/icons'

import { CNavGroup, CNavItem, CNavTitle } from '@coreui/react'

const _nav = [
  {
    component: CNavItem,
    name: 'Dashboard',
    to: '/dashboard',
    icon: <CIcon icon={cilSpeedometer} customClassName="nav-icon" />,
    badge: {
      color: 'info',
      text: 'NEW',
    },
  },  
  {
    component: CNavItem,
    name: 'Games',
    to: '/games',
    icon: <CIcon icon={cilCursor} customClassName="nav-icon" />,
  
  }

  // {
  //   component: CNavItem,
  //   name: 'Colors',
  //   to: '/theme/colors',
  //   icon: <CIcon icon={cilDrop} customClassName="nav-icon" />,
  // },
]

const _nav_administrator = [
  ..._nav,
  {
    component: CNavTitle,
    name: 'Admin',
  },
  {
    component: CNavItem,
    name: 'API keys',
    to: '/admin/api-keys',
    icon: <CIcon icon={cilPuzzle} customClassName="nav-icon" />,
    badge: {
      color: 'info',
      text: 'NEW',
    },
  },
]

export { _nav, _nav_administrator }
