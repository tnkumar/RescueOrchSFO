import { useState } from 'react'
import { trigger } from '../api'
import './TriggerButton.css'

export function TriggerButton() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [response, setResponse] = useState<string | null>(null)
  const [steps, setSteps] = useState<string[]>([])
  const [modalOpen, setModalOpen] = useState(false)

  const runTrigger = async () => {
    setLoading(true)
    setError(null)
    setResponse(null)
    setSteps([])
    setModalOpen(true)
    try {
      const data = await trigger.run()
      setResponse(data.response ?? 'No response.')
      setSteps(data.steps ?? [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Trigger failed')
    } finally {
      setLoading(false)
    }
  }

  const closeModal = () => {
    setModalOpen(false)
    setError(null)
    setResponse(null)
    setSteps([])
  }

  return (
    <>
      <button
        type="button"
        className="trigger-btn"
        onClick={runTrigger}
        disabled={loading}
        aria-label="Start rescue operation (call LLM with guidance)"
      >
        {loading ? '…' : '▶ Trigger'}
      </button>

      {modalOpen && (
        <div className="trigger-modal-backdrop" onClick={closeModal} aria-hidden="true">
          <div className="trigger-modal" onClick={(e) => e.stopPropagation()}>
            <div className="trigger-modal-header">
              <h3>Trigger – LLM response</h3>
              <button type="button" className="trigger-modal-close" onClick={closeModal} aria-label="Close">
                ×
              </button>
            </div>
            <div className="trigger-modal-body">
              {loading && <p className="trigger-loading">Calling LLM, then sending commands to world (1s gap)…</p>}
              {error && <p className="trigger-error">{error}</p>}
              {steps.length > 0 && (
                <div className="trigger-steps">
                  <h4>Commands sent to world</h4>
                  <ol className="trigger-steps-list">
                    {steps.map((step, i) => (
                      <li key={i}>{step}</li>
                    ))}
                  </ol>
                </div>
              )}
              {response && <pre className="trigger-response">{response}</pre>}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
