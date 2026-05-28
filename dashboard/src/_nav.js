import React from 'react'
import CIcon from '@coreui/icons-react'
import {
  cilCloudDownload,
  cilHistory,
  cilNotes,
  cilPencil,
  cilPuzzle,
  cilSpeedometer,
} from '@coreui/icons'
import { TbClockPin } from 'react-icons/tb'

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
]

const _nav_administrator = [
  ..._nav,
  {
    component: CNavTitle,
    name: 'Data',
  },
  {
    component: CNavItem,
    name: 'Data export',
    to: '/admin/exports',
    icon: <CIcon icon={cilCloudDownload} customClassName="nav-icon" />,
    badge: {
      color: 'info',
      text: 'NEW',
    },
  },
  {
    component: CNavItem,
    name: 'Export history',
    to: '/admin/exports/history',
    icon: <CIcon icon={cilHistory} customClassName="nav-icon" />,
  },
  {
    component: CNavTitle,
    name: 'Strategies',
  },
  {
    component: CNavItem,
    name: 'Strategy Editor',
    to: '/strategies/editor',
    icon: <CIcon icon={cilPencil} customClassName="nav-icon" />,
    badge: {
      color: 'info',
      text: 'NEW',
    },
  },
  {
    component: CNavItem,
    name: 'Asignación',
    to: '/admin/strategies/assignments',
    icon: <CIcon icon={cilNotes} customClassName="nav-icon" />,
    badge: {
      color: 'info',
      text: 'NEW',
    },
  },
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
  {
    component: CNavItem,
    name: 'KPI',
    to: '/admin/KPI',
    icon: <TbClockPin style={{ fontSize: '1.5em', marginRight: '10px' }} />,
  },
]

export { _nav, _nav_administrator }
