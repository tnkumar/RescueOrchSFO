import { useState } from 'react'
import { MavicPanel } from './components/MavicPanel'
import { TiagoPanel } from './components/TiagoPanel'
import { RobotCoordinatesBar } from './components/RobotCoordinatesBar'
import { ErrorBoundary } from './components/ErrorBoundary'
import { TriggerButton } from './components/TriggerButton'
import MissionControl from './components/MissionControl'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState<'control' | 'mission'>('mission')

  return (
    <div className="app">
      <header className="header">
        <h1>Rescue Command Center</h1>
        <span className="badge">SFO</span>
        <TriggerButton />
      </header>

      <nav className="tabs">
        <button
          className={`tab ${activeTab === 'mission' ? 'active' : ''}`}
          onClick={() => setActiveTab('mission')}
        >
          🚀 AI Mission Control
        </button>
        <button
          className={`tab ${activeTab === 'control' ? 'active' : ''}`}
          onClick={() => setActiveTab('control')}
        >
          🎮 Robot Control
        </button>
      </nav>

      <main className="main">
        {activeTab === 'mission' ? (
          <ErrorBoundary>
            <MissionControl />
          </ErrorBoundary>
        ) : (
          <>
            <RobotCoordinatesBar />
            <section className="panel mavic-panel">
              <MavicPanel />
            </section>
            <section className="panel tiago-panel">
              <TiagoPanel robotId="1" robotName="Tiago #1" />
            </section>
            <section className="panel tiago-panel">
              <TiagoPanel robotId="2" robotName="Tiago #2" />
            </section>
            <section className="panel tiago-panel">
              <TiagoPanel robotId="3" robotName="Tiago #3" />
            </section>
          </>
        )}
      </main>
    </div>
  )
}

export default App
