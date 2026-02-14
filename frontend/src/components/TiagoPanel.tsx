import { useState, useEffect, useCallback } from 'react'
import { tiago } from '../api'
import './TiagoPanel.css'

interface TiagoPanelProps {
  robotId: string
  robotName?: string
}

type TabType = 'base' | 'head' | 'torso' | 'arms' | 'grippers' | 'actions'

export function TiagoPanel({ robotId, robotName }: TiagoPanelProps) {
  const [status, setStatus] = useState<{ connected: boolean; position?: { x?: number; y?: number; z?: number } } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabType>('base')
  
  // Head state
  const [headPan, setHeadPan] = useState(0)
  const [headTilt, setHeadTilt] = useState(0)
  
  // Torso state
  const [torsoHeight, setTorsoHeight] = useState(0)
  
  // Arm states
  const [selectedArm, setSelectedArm] = useState<'left' | 'right'>('right')
  const [armJoints, setArmJoints] = useState<number[]>([0, 0, 0, 0, 0, 0, 0])
  const [moveX, setMoveX] = useState('0')
  const [moveY, setMoveY] = useState('0')

  const fetchStatus = useCallback(async () => {
    try {
      const s = await tiago.status(robotId)
      setStatus(s)
      setError(null)
    } catch {
      setError('Backend not reachable – start it with ./run.sh')
    }
  }, [robotId])

  useEffect(() => {
    fetchStatus()
    const id = setInterval(fetchStatus, 2000)
    return () => clearInterval(id)
  }, [fetchStatus])

  const handleHeadChange = (pan: number, tilt: number) => {
    setHeadPan(pan)
    setHeadTilt(tilt)
    tiago.head({ head_1: pan, head_2: tilt }, robotId).catch((e) => setError(e?.message || 'Command failed'))
  }

  const handleTorsoChange = (height: number) => {
    setTorsoHeight(height)
    tiago.torso({ height }, robotId).catch((e) => setError(e?.message || 'Command failed'))
  }

  const handleArmJointChange = (jointIndex: number, value: number) => {
    const newJoints = [...armJoints]
    newJoints[jointIndex] = value
    setArmJoints(newJoints)
    tiago.arm({ arm: selectedArm, joint_positions: newJoints }, robotId).catch((e) => setError(e?.message || 'Command failed'))
  }

  const handleGripper = (arm: 'left' | 'right', action: 'open' | 'close') => {
    tiago.gripper({ arm, action }, robotId).catch((e) => setError(e?.message || 'Command failed'))
  }

  const displayName = robotName || `Tiago #${robotId}`

  const tabs: { id: TabType; label: string }[] = [
    { id: 'base', label: 'Base' },
    { id: 'head', label: 'Head' },
    { id: 'torso', label: 'Torso' },
    { id: 'arms', label: 'Arms' },
    { id: 'grippers', label: 'Grippers' },
    { id: 'actions', label: 'Actions' },
  ]

  return (
    <div className="tiago-panel">
      <div className="panel-header">
        <h2>{displayName}</h2>
        <div className="status-row">
          <span className={`status-dot ${status?.connected ? 'ok' : 'err'}`} />
          <span className="status-text">{status?.connected ? 'Connected' : 'Offline'}</span>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="move-to-coords">
        <div className="move-to-row move-to-header">
          <span className="move-to-label">World position (absolute)</span>
        </div>
        <div className="move-to-row move-to-current">
          <span className="move-to-label">Current:</span>
          <span className="move-to-value">
            {status?.position != null && status.position.x != null && status.position.y != null
              ? `(${Number(status.position.x).toFixed(2)}, ${Number(status.position.y).toFixed(2)}) m`
              : '—'}
          </span>
        </div>
        <div className="move-to-row">
          <span className="move-to-label">Move to:</span>
          <input type="number" step="any" placeholder="X" value={moveX} onChange={(e) => setMoveX(e.target.value)} aria-label="X (world)" />
          <input type="number" step="any" placeholder="Y" value={moveY} onChange={(e) => setMoveY(e.target.value)} aria-label="Y (world)" />
          <button
            className="btn btn-move-to"
            onClick={() => {
              const x = parseFloat(moveX) || 0
              const y = parseFloat(moveY) || 0
              tiago.moveTo(x, y, robotId)
                .then(() => setError(null))
                .catch((e) => setError(e?.message || 'Move failed'))
            }}
          >
            Go
          </button>
        </div>
      </div>

      <div className="tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="controls">
        {activeTab === 'base' && (
          <>
            <div className="action-buttons">
              <button onClick={() => tiago.action('stop', robotId)} className="btn btn-stop">
                Stop
              </button>
            </div>
            <p className="hint">Move {displayName} only via &quot;Move to&quot; X, Y and <strong>Go</strong> above. Use Stop to halt.</p>
          </>
        )}

        {activeTab === 'head' && (
          <div className="head-controls">
            <div className="control-group">
              <label>Head Pan (Left/Right)</label>
              <div className="slider-control">
                <button onClick={() => handleHeadChange(-1.57, headTilt)} className="btn btn-secondary">◀</button>
                <input
                  type="range"
                  min="-1.57"
                  max="1.57"
                  step="0.1"
                  value={headPan}
                  onChange={(e) => handleHeadChange(parseFloat(e.target.value), headTilt)}
                  className="slider"
                />
                <button onClick={() => handleHeadChange(1.57, headTilt)} className="btn btn-secondary">▶</button>
              </div>
              <span className="value-display">{headPan.toFixed(2)} rad</span>
            </div>
            <div className="control-group">
              <label>Head Tilt (Up/Down)</label>
              <div className="slider-control">
                <button onClick={() => handleHeadChange(headPan, -1.57)} className="btn btn-secondary">▼</button>
                <input
                  type="range"
                  min="-1.57"
                  max="1.57"
                  step="0.1"
                  value={headTilt}
                  onChange={(e) => handleHeadChange(headPan, parseFloat(e.target.value))}
                  className="slider"
                />
                <button onClick={() => handleHeadChange(headPan, 1.57)} className="btn btn-secondary">▲</button>
              </div>
              <span className="value-display">{headTilt.toFixed(2)} rad</span>
            </div>
            <button onClick={() => handleHeadChange(0, 0)} className="btn btn-secondary">Reset Head</button>
          </div>
        )}

        {activeTab === 'torso' && (
          <div className="torso-controls">
            <div className="control-group">
              <label>Torso Lift Height</label>
              <div className="slider-control">
                <button onClick={() => handleTorsoChange(0)} className="btn btn-secondary">▼</button>
                <input
                  type="range"
                  min="0"
                  max="0.35"
                  step="0.01"
                  value={torsoHeight}
                  onChange={(e) => handleTorsoChange(parseFloat(e.target.value))}
                  className="slider"
                />
                <button onClick={() => handleTorsoChange(0.35)} className="btn btn-secondary">▲</button>
              </div>
              <span className="value-display">{(torsoHeight * 100).toFixed(0)} cm</span>
            </div>
            <div className="preset-buttons">
              <button onClick={() => handleTorsoChange(0)} className="btn btn-secondary">Low</button>
              <button onClick={() => handleTorsoChange(0.175)} className="btn btn-secondary">Mid</button>
              <button onClick={() => handleTorsoChange(0.35)} className="btn btn-secondary">High</button>
            </div>
          </div>
        )}

        {activeTab === 'arms' && (
          <div className="arm-controls">
            <div className="arm-selector">
              <button
                className={`btn ${selectedArm === 'left' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setSelectedArm('left')}
              >
                Left Arm
              </button>
              <button
                className={`btn ${selectedArm === 'right' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setSelectedArm('right')}
              >
                Right Arm
              </button>
            </div>
            <div className="joint-controls">
              {[0, 1, 2, 3, 4, 5, 6].map((jointIndex) => (
                <div key={jointIndex} className="control-group">
                  <label>Joint {jointIndex + 1}</label>
                  <div className="slider-control">
                    <button
                      onClick={() => handleArmJointChange(jointIndex, armJoints[jointIndex] - 0.1)}
                      className="btn btn-secondary"
                    >
                      −
                    </button>
                    <input
                      type="range"
                      min="-3.14"
                      max="3.14"
                      step="0.1"
                      value={armJoints[jointIndex]}
                      onChange={(e) => handleArmJointChange(jointIndex, parseFloat(e.target.value))}
                      className="slider"
                    />
                    <button
                      onClick={() => handleArmJointChange(jointIndex, armJoints[jointIndex] + 0.1)}
                      className="btn btn-secondary"
                    >
                      +
                    </button>
                  </div>
                  <span className="value-display">{armJoints[jointIndex].toFixed(2)} rad</span>
                </div>
              ))}
            </div>
            <div className="action-buttons">
              <button onClick={() => tiago.action('home_arms', robotId)} className="btn btn-secondary">
                Home Arms
              </button>
              <button onClick={() => setArmJoints([0, 0, 0, 0, 0, 0, 0])} className="btn btn-secondary">
                Reset Joints
              </button>
            </div>
          </div>
        )}

        {activeTab === 'grippers' && (
          <div className="gripper-controls">
            <div className="gripper-group">
              <h3>Left Gripper</h3>
              <div className="gripper-buttons">
                <button
                  onClick={() => handleGripper('left', 'open')}
                  className="btn btn-secondary"
                >
                  Open
                </button>
                <button
                  onClick={() => handleGripper('left', 'close')}
                  className="btn btn-secondary"
                >
                  Close
                </button>
              </div>
            </div>
            <div className="gripper-group">
              <h3>Right Gripper</h3>
              <div className="gripper-buttons">
                <button
                  onClick={() => handleGripper('right', 'open')}
                  className="btn btn-secondary"
                >
                  Open
                </button>
                <button
                  onClick={() => handleGripper('right', 'close')}
                  className="btn btn-secondary"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'actions' && (
          <div className="action-controls">
            <div className="action-buttons-grid">
              <button onClick={() => tiago.action('stop', robotId)} className="btn btn-stop">
                Stop All
              </button>
              <button onClick={() => tiago.action('home_arms', robotId)} className="btn btn-secondary">
                Home Arms
              </button>
              <button onClick={() => handleHeadChange(0, 0)} className="btn btn-secondary">
                Reset Head
              </button>
              <button onClick={() => handleTorsoChange(0)} className="btn btn-secondary">
                Lower Torso
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
