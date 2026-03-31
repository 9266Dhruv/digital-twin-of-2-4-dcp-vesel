import { useEffect, useState, useRef, useCallback } from 'react';

const WS_BASE = 'ws://localhost:8000/ws';
const API_URL = 'http://localhost:8000';

/** Get stored JWT token */
const getToken = () => localStorage.getItem('dcp_token') || '';

/** Build auth headers for REST calls */
const authHeaders = (extra = {}) => {
    const token = getToken();
    const headers = { ...extra };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return headers;
};

/**
 * WebSocket hook for real-time telemetry streaming
 */
export const useTelemetry = () => {
    const [telemetry, setTelemetry] = useState(null);
    const [audit, setAudit] = useState([]);
    const [tempHistory, setTempHistory] = useState([]);
    const [pressureHistory, setPressureHistory] = useState([]);
    const [status, setStatus] = useState('DISCONNECTED');
    const ws = useRef(null);
    const retryCount = useRef(0);
    const maxRetries = 5;

    useEffect(() => {
        let reconnectTimer = null;

        const connect = () => {
            const token = getToken();
            if (!token) {
                console.warn('No auth token found. Cannot connect WebSocket.');
                setStatus('NO_AUTH');
                return;
            }

            const wsUrl = `${WS_BASE}?token=${encodeURIComponent(token)}`;

            try {
                ws.current = new WebSocket(wsUrl);
            } catch (err) {
                console.error('WebSocket creation failed:', err);
                setStatus('ERROR');
                return;
            }

            ws.current.onopen = () => {
                setStatus('CONNECTED');
                retryCount.current = 0; // Reset retry counter on success
            };

            ws.current.onclose = (event) => {
                setStatus('DISCONNECTED');

                // Code 4001 = explicit auth rejection from backend
                if (event.code === 4001) {
                    console.warn('WebSocket auth rejected (code 4001). Clearing session.');
                    localStorage.removeItem('dcp_token');
                    localStorage.removeItem('dcp_role');
                    localStorage.removeItem('dcp_username');
                    window.location.reload();
                    return;
                }

                retryCount.current++;

                // After several failed attempts, validate the token via REST
                if (retryCount.current >= 3) {
                    fetch(`${API_URL}/api/auth/me`, { headers: authHeaders() })
                        .then(res => {
                            if (!res.ok) {
                                // Token is invalid — clear and force re-login
                                console.warn('Token validation failed after WS retries. Clearing session.');
                                localStorage.removeItem('dcp_token');
                                localStorage.removeItem('dcp_role');
                                localStorage.removeItem('dcp_username');
                                window.location.reload();
                            } else {
                                // Token is valid — keep retrying with backoff
                                const delay = Math.min(retryCount.current * 2000, 15000);
                                reconnectTimer = setTimeout(connect, delay);
                            }
                        })
                        .catch(() => {
                            // Backend unreachable — retry with backoff
                            const delay = Math.min(retryCount.current * 2000, 15000);
                            reconnectTimer = setTimeout(connect, delay);
                        });
                    return;
                }

                // Normal retry with increasing delay
                const delay = Math.min(retryCount.current * 1000, 5000);
                reconnectTimer = setTimeout(connect, delay);
            };

            ws.current.onerror = (error) => {
                console.error('WebSocket error:', error);
                setStatus('ERROR');
            };

            ws.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    // Backend sends {telemetry: {...}, audit: [...]}
                    setTelemetry(data.telemetry || data);

                    if (Array.isArray(data.audit)) {
                        setAudit(data.audit);
                    }

                    // Track temperature history
                    const tempValue = data?.telemetry?.temp ?? data?.temp;
                    if (typeof tempValue === 'number') {
                        setTempHistory((prev) => {
                            const next = [...prev, tempValue];
                            return next.slice(-60); // Keep last 60 samples
                        });
                    }

                    // Track pressure history
                    const pressureValue = data?.telemetry?.pressure ?? data?.pressure;
                    if (typeof pressureValue === 'number') {
                        setPressureHistory((prev) => {
                            const next = [...prev, pressureValue];
                            return next.slice(-60);
                        });
                    }
                } catch (e) {
                    console.error('Error parsing telemetry:', e);
                }
            };
        };

        connect();
        return () => {
            if (reconnectTimer) clearTimeout(reconnectTimer);
            ws.current?.close();
        };
    }, []);

    const sendControl = useCallback((command) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(command));
        } else {
            console.warn('WebSocket not connected, command not sent:', command);
        }
    }, []);

    return {
        telemetry,
        audit,
        tempHistory,
        pressureHistory,
        status,
        sendControl
    };
};


/**
 * REST API functions for batch reports and data retrieval
 */
export const api = {
    // Get current reactor status
    getStatus: async () => {
        const response = await fetch(`${API_URL}/api/status`, { headers: authHeaders() });
        return response.json();
    },

    // Get detailed recipe status
    getRecipeStatus: async () => {
        const response = await fetch(`${API_URL}/api/recipe/status`, { headers: authHeaders() });
        return response.json();
    },

    // Get recipe steps
    getRecipeSteps: async () => {
        const response = await fetch(`${API_URL}/api/recipe/steps`, { headers: authHeaders() });
        return response.json();
    },

    // Start recipe
    startRecipe: async () => {
        const response = await fetch(`${API_URL}/api/recipe/start`, { method: 'POST', headers: authHeaders() });
        return response.json();
    },

    // Stop recipe
    stopRecipe: async () => {
        const response = await fetch(`${API_URL}/api/recipe/stop`, { method: 'POST', headers: authHeaders() });
        return response.json();
    },

    // Reset recipe
    resetRecipe: async () => {
        const response = await fetch(`${API_URL}/api/recipe/reset`, { method: 'POST', headers: authHeaders() });
        return response.json();
    },

    // Get batch summary
    getBatchSummary: async () => {
        const response = await fetch(`${API_URL}/api/batch/summary`, { headers: authHeaders() });
        return response.json();
    },

    // Generate and download batch report
    downloadBatchReport: async () => {
        const response = await fetch(`${API_URL}/api/batch/report`, { headers: authHeaders() });
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `batch_report_${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            return true;
        }
        return false;
    },

    // List all batch reports
    listBatchReports: async () => {
        const response = await fetch(`${API_URL}/api/batch/reports`, { headers: authHeaders() });
        return response.json();
    },

    // Download specific batch report
    downloadReport: async (filename) => {
        const response = await fetch(`${API_URL}/api/batch/report/${filename}`, { headers: authHeaders() });
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            return true;
        }
        return false;
    },

    // Get telemetry history
    getTelemetryHistory: async () => {
        const response = await fetch(`${API_URL}/api/telemetry/history`, { headers: authHeaders() });
        return response.json();
    },

    // Get events log
    getEvents: async () => {
        const response = await fetch(`${API_URL}/api/events`, { headers: authHeaders() });
        return response.json();
    },

    // Get control actions log
    getControlActions: async () => {
        const response = await fetch(`${API_URL}/api/control-actions`, { headers: authHeaders() });
        return response.json();
    },

    // Send control command
    sendControl: async (command) => {
        const response = await fetch(`${API_URL}/api/control`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(command)
        });
        return response.json();
    },

    // Get faults status
    getFaults: async () => {
        const response = await fetch(`${API_URL}/api/faults`, { headers: authHeaders() });
        return response.json();
    },

    // Toggle fault
    toggleFault: async (faultName) => {
        const response = await fetch(`${API_URL}/api/fault/${faultName}/toggle`, { method: 'POST', headers: authHeaders() });
        return response.json();
    },

    // Get interlock status
    getInterlocks: async () => {
        const response = await fetch(`${API_URL}/api/interlocks`, { headers: authHeaders() });
        return response.json();
    }
};


/**
 * Hook for batch report management
 */
export const useBatchReports = () => {
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchReports = useCallback(async () => {
        setLoading(true);
        try {
            const data = await api.listBatchReports();
            setReports(data.reports || []);
            setError(null);
        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const downloadReport = useCallback(async (filename) => {
        return api.downloadReport(filename);
    }, []);

    const generateReport = useCallback(async () => {
        const success = await api.downloadBatchReport();
        if (success) {
            await fetchReports(); // Refresh list
        }
        return success;
    }, [fetchReports]);

    return {
        reports,
        loading,
        error,
        fetchReports,
        downloadReport,
        generateReport
    };
};
