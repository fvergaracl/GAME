import React from 'react'
import CIcon from '@coreui/icons-react'
import {
  cilCloudDownload,
  cilHistory,
  cilLibrary,
  cilNotes,
  cilPencil,
  cilPuzzle,
  cilSpeedometer,
} from '@coreui/icons'
import { TbClockPin } from 'react-icons/tb'

import { CNavGroup, CNavItem, CNavTitle } from '@coreui/react'

// ``name`` holds an i18next key under the ``app:nav.*`` namespace; it is
// translated at render time in AppSidebarNav so switching languages
// relabels the sidebar without rebuilding this config.
const _nav = [
  {
    component: CNavItem,
    name: 'nav.dashboard',
    to: '/dashboard',
    icon: <CIcon icon={cilSpeedometer} customClassName="nav-icon" />,
  },
]

const _nav_administrator = [
  ..._nav,
  {
    component: CNavTitle,
    name: 'nav.dataTitle',
  },
  {
    component: CNavItem,
    name: 'nav.dataExport',
    to: '/admin/exports',
    icon: <CIcon icon={cilCloudDownload} customClassName="nav-icon" />,
  },
  {
    component: CNavItem,
    name: 'nav.exportHistory',
    to: '/admin/exports/history',
    icon: <CIcon icon={cilHistory} customClassName="nav-icon" />,
  },
  {
    component: CNavTitle,
    name: 'nav.strategiesTitle',
  },
  {
    component: CNavItem,
    name: 'nav.myStrategies',
    to: '/strategies/library',
    icon: <CIcon icon={cilLibrary} customClassName="nav-icon" />,
  },
  {
    component: CNavItem,
    name: 'nav.strategyEditor',
    to: '/strategies/editor',
    icon: <CIcon icon={cilPencil} customClassName="nav-icon" />,
  },
  {
    component: CNavItem,
    name: 'nav.assignments',
    to: '/admin/strategies/assignments',
    icon: <CIcon icon={cilNotes} customClassName="nav-icon" />,
  },
  {
    component: CNavTitle,
    name: 'nav.adminTitle',
  },
  {
    component: CNavItem,
    name: 'nav.apiKeys',
    to: '/admin/api-keys',
    icon: <CIcon icon={cilPuzzle} customClassName="nav-icon" />,
  },
]

export { _nav, _nav_administrator }
