// Sprint 5: saveable simulation scenarios. A "scenario" is the full set of
// test inputs (ids, event data, mock overrides, accumulated-field values,
// single/cumulative mode + step). Designers iterate on the same handful of
// inputs over and over - saving them as named presets means they stop
// re-typing "user with 5 measurements, 30s avg time" every session.
//
// Persistence is localStorage (per browser), not the backend: scenarios are
// a personal scratchpad, not shared strategy state, and keeping them client
// side avoids a new table + endpoint for what is essentially a convenience.

import React, { useCallback, useEffect, useState } from 'react'
import PropTypes from 'prop-types'
import { useTranslation } from 'react-i18next'
import { CButton, CFormInput, CFormSelect } from '@coreui/react'

const STORAGE_KEY = 'game:simScenarios'

function readScenarios() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    // Corrupt / unavailable storage - degrade to an empty list rather
    // than crashing the editor.
    return []
  }
}

function writeScenarios(list) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
  } catch {
    // Quota / private-mode errors are non-fatal; the in-memory list still
    // works for the current session.
  }
}

export default function SimulationScenarios({ current, onLoad }) {
  const { t } = useTranslation('editor')
  const [scenarios, setScenarios] = useState([])
  const [selected, setSelected] = useState('')
  const [newName, setNewName] = useState('')

  useEffect(() => {
    setScenarios(readScenarios())
  }, [])

  const persist = useCallback((list) => {
    setScenarios(list)
    writeScenarios(list)
  }, [])

  const handleSave = useCallback(() => {
    const name = newName.trim()
    if (!name) return
    // Overwrite an existing preset of the same name so re-saving updates
    // in place instead of creating duplicates.
    const without = scenarios.filter((s) => s.name !== name)
    persist([...without, { name, scenario: current }])
    setNewName('')
    setSelected(name)
  }, [newName, scenarios, current, persist])

  const handleLoad = useCallback(() => {
    const found = scenarios.find((s) => s.name === selected)
    if (found) onLoad(found.scenario)
  }, [scenarios, selected, onLoad])

  const handleDelete = useCallback(() => {
    if (!selected) return
    persist(scenarios.filter((s) => s.name !== selected))
    setSelected('')
  }, [scenarios, selected, persist])

  return (
    <div className="mb-3 p-2 rounded" style={{ background: 'var(--cui-tertiary-bg)' }}>
      <div className="small fw-semibold mb-2">{t('simulate.scenarios.title')}</div>

      <div className="d-flex gap-2 mb-2">
        <CFormSelect
          size="sm"
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          aria-label={t('simulate.scenarios.selectLabel')}
        >
          <option value="">{t('simulate.scenarios.selectPlaceholder')}</option>
          {scenarios.map((s) => (
            <option key={s.name} value={s.name}>
              {s.name}
            </option>
          ))}
        </CFormSelect>
        <CButton
          size="sm"
          color="secondary"
          variant="outline"
          disabled={!selected}
          onClick={handleLoad}
        >
          {t('simulate.scenarios.load')}
        </CButton>
        <CButton
          size="sm"
          color="danger"
          variant="outline"
          disabled={!selected}
          onClick={handleDelete}
        >
          {t('simulate.scenarios.delete')}
        </CButton>
      </div>

      <div className="d-flex gap-2">
        <CFormInput
          size="sm"
          type="text"
          value={newName}
          placeholder={t('simulate.scenarios.namePlaceholder')}
          aria-label={t('simulate.scenarios.namePlaceholder')}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault()
              handleSave()
            }
          }}
        />
        <CButton size="sm" color="secondary" disabled={!newName.trim()} onClick={handleSave}>
          {t('simulate.scenarios.save')}
        </CButton>
      </div>
    </div>
  )
}

SimulationScenarios.propTypes = {
  current: PropTypes.object.isRequired,
  onLoad: PropTypes.func.isRequired,
}
