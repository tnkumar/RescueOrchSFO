import { useState, useEffect, useCallback } from 'react'
import { mavic, tiago } from '../api'
import './RobotCoordinatesBar.css'

interface Position {
  x?: number
  y?: number
  z?: number
}

export function RobotCoordinatesBar() {
  const [mavicPos, setMavicPos] = useState<Position | null>(null)
  const [tiago1Pos, setTiago1Pos] = useState<Position | null>(null)
  const [tiago2Pos, setTiago2Pos] = useState<Position | null>(null)
  const [tiago3Pos, setTiago3Pos] = useState<Position | null>(null)
  const [error, setError] = useState<string | null>(null)

  const fetchPositions = useCallback(async () => {
    try {
      const [mavicStatus, t1, t2, t3] = await Promise.all([
        mavic.status(),
        tiago.status('1'),
        tiago.status('2'),
        tiago.status('3'),
      ])
      const m = mavicStatus as { flying?: boolean; altitude?: number; position?: Position }
      setMavicPos(
        m.position ?? (m.flying ? { x: 0, y: 0, z: m.altitude ?? 0 } : null)
      )
      const toPos = (s: unknown) => (s as { position?: Position }).position ?? null
      setTiago1Pos(toPos(t1))
      setTiago2Pos(toPos(t2))
      setTiago3Pos(toPos(t3))
      setError(null)
    } catch (e) {
      setError('Backend unreachable')
    }
  }, [])

  useEffect(() => {
    fetchPositions()
    const id = setInterval(fetchPositions, 1500)
    return () => clearInterval(id)
  }, [fetchPositions])

  const fmt = (p: Position | null) => {
    if (!p) return '—'
    const x = p.x != null ? p.x.toFixed(2) : '?'
    const y = p.y != null ? p.y.toFixed(2) : '?'
    const z = p.z != null ? p.z.toFixed(2) : '?'
    return `(${x}, ${y}, ${z})`
  }

  if (error) {
    return (
      <div className="robot-coordinates-bar error">
        <span>{error}</span>
      </div>
    )
  }

  return (
    <div className="robot-coordinates-bar">
      <span className="coord-label">Mavic:</span>
      <span className="coord-value">{fmt(mavicPos)}</span>
      <span className="coord-sep">|</span>
      <span className="coord-label">Tiago #1:</span>
      <span className="coord-value">{fmt(tiago1Pos)}</span>
      <span className="coord-sep">|</span>
      <span className="coord-label">Tiago #2:</span>
      <span className="coord-value">{fmt(tiago2Pos)}</span>
      <span className="coord-sep">|</span>
      <span className="coord-label">Tiago #3:</span>
      <span className="coord-value">{fmt(tiago3Pos)}</span>
    </div>
  )
}
