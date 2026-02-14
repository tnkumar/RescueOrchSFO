import { useState, useEffect } from 'react';
import './MissionControl.css';

const API_URL = 'http://127.0.0.1:8000';

interface Incident {
    id: string;
    type: string;
    location: { x: number; y: number; z: number };
    severity: string;
    description?: string;
    timestamp: number;
}

interface RobotStatus {
    status: string;
    task: string | null;
    current_step: number;
    total_steps: number;
    position: { x: number; y: number; z: number };
}

interface MissionStatus {
    active: boolean;
    incidents: {
        total: number;
        list: Incident[];
    };
    robots: {
        [key: string]: RobotStatus;
    };
}

export default function MissionControl() {
    const [missionActive, setMissionActive] = useState(false);
    const [missionStatus, setMissionStatus] = useState<MissionStatus | null>(null);
    const [lastAIAnalysis, setLastAIAnalysis] = useState<string>('');
    const [loading, setLoading] = useState(false);

    // Poll mission status every 2 seconds
    useEffect(() => {
        if (missionActive) {
            const interval = setInterval(fetchMissionStatus, 2000);
            return () => clearInterval(interval);
        }
    }, [missionActive]);

    const fetchMissionStatus = async () => {
        try {
            const response = await fetch(`${API_URL}/mission/status`);
            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            console.log('Mission status fetched:', data);

            // Validate data structure to prevent crashes
            if (!data || typeof data !== 'object') {
                console.error('Invalid status data received:', data);
                return;
            }

            console.log('Robots:', data.robots);
            console.log('Incidents:', data.incidents);
            setMissionStatus(data);
        } catch (error) {
            console.error('Failed to fetch mission status:', error);
        }
    };

    const startMission = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_URL}/mission/start`, { method: 'POST' });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('Mission started successfully:', data);

            // Set mission active FIRST
            setMissionActive(true);

            // Then fetch status
            await fetchMissionStatus();

            // Alert last
            setTimeout(() => alert(`✅ ${data.message || 'Mission started successfully'}`), 100);

        } catch (error) {
            console.error('Start mission error:', error);
            alert(`❌ Failed to start mission: ${error}`);
        } finally {
            setLoading(false);
        }
    };

    const stopMission = async () => {
        setLoading(true);
        try {
            await fetch(`${API_URL}/mission/stop`, { method: 'POST' });
            setMissionActive(false);
            setMissionStatus(null);
            alert('✅ Mission stopped');
        } catch (error) {
            alert('❌ Failed to stop mission');
        } finally {
            setLoading(false);
        }
    };

    const reportTestIncident = async (type: string) => {
        const incidents = {
            fire: {
                type: 'fire',
                location: { x: 1.63, y: 0.92, z: 1.15 },
                severity: 'critical',
                description: 'Fire near stove with LPG cylinder'
            },
            victim: {
                type: 'victim',
                location: { x: -0.65, y: -1.43, z: 0.0 },
                severity: 'high',
                description: 'Person trapped in room'
            },
            gas_leak: {
                type: 'gas_leak',
                location: { x: 1.3, y: 0.22, z: 0.0 },
                severity: 'critical',
                description: 'LPG cylinder valve open'
            }
        };

        const incident = incidents[type as keyof typeof incidents];
        if (!incident) return;

        setLoading(true);
        try {
            const response = await fetch(`${API_URL}/mission/incident/report`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(incident)
            });
            const data = await response.json();
            if (data.ai_analysis?.analysis) {
                setLastAIAnalysis(data.ai_analysis.analysis);
            }
            alert(`✅ ${type.toUpperCase()} incident reported!`);
            fetchMissionStatus();
        } catch (error) {
            alert('❌ Failed to report incident');
        } finally {
            setLoading(false);
        }
    };

    const analyzeScene = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_URL}/mavic/camera/analyze`, {
                method: 'POST'
            });
            const data = await response.json();

            if (data.status === 'incident_reported') {
                alert(`🚨 ALERT: AI Detected ${data.incident.type.toUpperCase()}! Robot assigned.`);
                if (data.analysis?.key_insights) {
                    setLastAIAnalysis(data.analysis.key_insights);
                }
                fetchMissionStatus();
            } else {
                alert('✅ Scene Analyzed: No threats detected.');
                if (data.analysis) {
                    // Format analysis for display
                    setLastAIAnalysis(`Scanned: ${data.analysis.scene_description || 'Clear'}`);
                }
            }
        } catch (error) {
            console.error('Analysis error:', error);
            alert('❌ Failed to analyze scene');
        } finally {
            setLoading(false);
        }
    };

    const getSeverityColor = (severity: string) => {
        switch (severity.toLowerCase()) {
            case 'critical': return '#ef4444';
            case 'high': return '#f97316';
            case 'medium': return '#eab308';
            case 'low': return '#22c55e';
            default: return '#6b7280';
        }
    };

    const getProgressPercentage = (robot: RobotStatus) => {
        if (robot.total_steps === 0) return 0;
        return Math.round((robot.current_step / robot.total_steps) * 100);
    };

    return (
        <div className="mission-control">
            <header className="mission-header">
                <h1>🚀 AI Rescue Mission Control</h1>
                <p>Gemini 2.5-flash Coordinated Operations</p>
            </header>

            {missionActive && (
                <div className="camera-feed-section">
                    <h2>📹 Mavic Drone Camera Feed</h2>
                    <img
                        src={`${API_URL}/mavic/camera/stream`}
                        alt="Mavic Camera Feed"
                        className="camera-feed"
                    />
                    <div className="camera-controls">
                        <button
                            className="btn btn-analyze"
                            onClick={analyzeScene}
                            disabled={loading}
                        >
                            📸 Analyze Scene (AI Scan)
                        </button>
                    </div>
                </div>
            )}

            <div className="control-panel">
                {!missionActive ? (
                    <button
                        className="btn btn-start"
                        onClick={startMission}
                        disabled={loading}
                    >
                        {loading ? '⏳ Starting...' : '▶️ Start Mission'}
                    </button>
                ) : (
                    <button
                        className="btn btn-stop"
                        onClick={stopMission}
                        disabled={loading}
                    >
                        {loading ? '⏳ Stopping...' : '⏹️ Stop Mission'}
                    </button>
                )}

                {missionActive && (
                    <div className="incident-buttons">
                        <button
                            className="btn btn-incident fire"
                            onClick={() => reportTestIncident('fire')}
                            disabled={loading}
                        >
                            🔥 Report Fire
                        </button>
                        <button
                            className="btn btn-incident victim"
                            onClick={() => reportTestIncident('victim')}
                            disabled={loading}
                        >
                            🆘 Report Victim
                        </button>
                        <button
                            className="btn btn-incident gas"
                            onClick={() => reportTestIncident('gas_leak')}
                            disabled={loading}
                        >
                            ⚠️ Report Gas Leak
                        </button>
                    </div>
                )}
            </div>

            {lastAIAnalysis && (
                <div className="ai-analysis">
                    <h3>🤖 Gemini AI Analysis</h3>
                    <p>{lastAIAnalysis}</p>
                </div>
            )}

            {missionStatus && (
                <>
                    <div className="incidents-section">
                        <h2>📍 Detected Incidents ({missionStatus?.incidents?.total || 0})</h2>
                        {missionStatus?.incidents?.list && Array.isArray(missionStatus.incidents.list) && missionStatus.incidents.list.length > 0 ? (
                            <div className="incidents-grid">
                                {missionStatus.incidents.list.map((incident) => (
                                    <div key={incident?.id || Math.random()} className="incident-card">
                                        <div className="incident-header">
                                            <span className="incident-type">{(incident?.type || 'UNKNOWN').toUpperCase()}</span>
                                            <span
                                                className="incident-severity"
                                                style={{ backgroundColor: getSeverityColor(incident?.severity || 'low') }}
                                            >
                                                {incident?.severity || 'LOW'}
                                            </span>
                                        </div>
                                        <div className="incident-location">
                                            📍 ({incident?.location?.x?.toFixed(2) || '0.00'}, {incident?.location?.y?.toFixed(2) || '0.00'})
                                        </div>
                                        {incident?.description && (
                                            <div className="incident-description">{incident.description}</div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="loading-text">
                                No incidents reported yet. Click the buttons above to report incidents.
                            </p>
                        )}
                    </div>

                    <div className="robots-section">
                        <h2>🤖 Robot Status</h2>
                        {missionStatus?.robots && typeof missionStatus.robots === 'object' && Object.keys(missionStatus.robots).length > 0 ? (
                            <div className="robots-grid">
                                {Object.entries(missionStatus.robots).map(([robotId, robot]) => {
                                    if (!robot) return null;
                                    const progress = getProgressPercentage(robot);
                                    return (
                                        <div key={robotId} className="robot-card">
                                            <div className="robot-header">
                                                <h3>{(robotId || 'ROBOT').toUpperCase()}</h3>
                                                <span className={`robot-status ${robot?.status || 'unknown'}`}>
                                                    {robot?.status || 'UNKNOWN'}
                                                </span>
                                            </div>

                                            {robot?.task && (
                                                <div className="robot-task">
                                                    <strong>Task:</strong> {robot.task}
                                                </div>
                                            )}

                                            {(robot?.total_steps || 0) > 0 && (
                                                <div className="robot-progress">
                                                    <div className="progress-bar">
                                                        <div
                                                            className="progress-fill"
                                                            style={{ width: `${progress}%` }}
                                                        />
                                                    </div>
                                                    <div className="progress-text">
                                                        {robot?.current_step || 0}/{robot?.total_steps || 0} steps ({progress}%)
                                                    </div>
                                                </div>
                                            )}

                                            <div className="robot-position">
                                                📍 Position: ({robot?.position?.x?.toFixed(2) || '0.00'}, {robot?.position?.y?.toFixed(2) || '0.00'})
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <p className="loading-text">
                                Loading robot status...
                            </p>
                        )}
                    </div>
                </>
            )}

            {!missionActive && !missionStatus && (
                <div className="welcome-message">
                    <h2>👋 Welcome to AI Rescue Mission Control</h2>
                    <p>Click "Start Mission" to begin AI-orchestrated rescue operations</p>
                    <ul>
                        <li>✅ Gemini 2.5-flash AI analyzes incidents</li>
                        <li>✅ Intelligent robot assignment</li>
                        <li>✅ Real-time Webots integration</li>
                        <li>✅ Live progress tracking</li>
                    </ul>
                </div>
            )}
        </div>
    );
}
