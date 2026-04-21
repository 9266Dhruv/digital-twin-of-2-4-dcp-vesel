import React, { useState } from 'react';
import { User, KeyRound, Eye, EyeOff, Shield, Loader2 } from 'lucide-react';
import Dither from './Dither';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const LoginPage = ({ onLogin }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [focusedField, setFocusedField] = useState(null);

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            const response = await fetch(`${API_URL}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                setError(errData.detail || 'Invalid credentials. Please try again.');
                setIsLoading(false);
                return;
            }

            const data = await response.json();
            // Store token for WebSocket and REST API usage
            localStorage.setItem('dcp_token', data.access_token);
            localStorage.setItem('dcp_role', data.role);
            localStorage.setItem('dcp_username', data.username);

            const nameMap = { 'worker': 'Operator', 'owner': 'Himanshu Patel' };
            onLogin({
                name: nameMap[data.username] || data.username,
                role: data.role,
                token: data.access_token,
            });
        } catch (err) {
            setError('Cannot connect to server. Is the backend running?');
            setIsLoading(false);
        }
    };

    const fillCredentials = (user, pass) => {
        setUsername(user);
        setPassword(pass);
        setError('');
    };

    return (
        <div style={{
            position: 'fixed', inset: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: "'Inter', -apple-system, sans-serif",
            background: '#000', overflow: 'hidden'
        }}>

            {/* Keyframe Animations */}
            <style>{`
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        @keyframes ringPulse { 0% { transform: scale(0.8); opacity: 0.6; } 100% { transform: scale(1.8); opacity: 0; } }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes shake { 0%, 100% { transform: translateX(0); } 25% { transform: translateX(-6px); } 75% { transform: translateX(6px); } }
      `}</style>

            {/* Dither Background */}
            <div style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
                <Dither
                    waveColor={[0.5, 0.5, 0.5]}
                    disableAnimation={false}
                    enableMouseInteraction={true}
                    mouseRadius={0.3}
                    colorNum={4}
                    waveAmplitude={0.3}
                    waveFrequency={3}
                    waveSpeed={0.05}
                />
            </div>

            {/* Main Container */}
            <div style={{
                position: 'relative', zIndex: 10,
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 24
            }}>

                {/* Login Card - Semi-transparent with blur */}
                <div style={{
                    position: 'relative', width: 400, padding: '44px 40px',
                    background: 'rgba(0, 0, 0, 0.6)',
                    backdropFilter: 'blur(16px)', WebkitBackdropFilter: 'blur(16px)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: 16,
                    boxShadow: '0 20px 50px rgba(0,0,0,0.4)'
                }}>

                    {/* Header */}
                    <div style={{ textAlign: 'center', marginBottom: 36 }}>
                        {/* Logo with rings */}
                        <div style={{ position: 'relative', width: 72, height: 72, margin: '0 auto 20px' }}>
                            <div style={{
                                position: 'absolute', top: '50%', left: '50%',
                                transform: 'translate(-50%, -50%)',
                                width: 48, height: 48,
                                background: 'rgba(255, 255, 255, 0.08)',
                                borderRadius: '50%',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                border: '1.5px solid rgba(255, 255, 255, 0.25)'
                            }}>
                                <Shield size={24} color="#fff" strokeWidth={1.5} />
                            </div>
                            {[1, 2, 3].map(i => (
                                <div key={i} style={{
                                    position: 'absolute', top: '50%', left: '50%',
                                    width: 48 + i * 16, height: 48 + i * 16,
                                    marginTop: -(24 + i * 8), marginLeft: -(24 + i * 8),
                                    border: `1px solid rgba(255, 255, 255, ${0.2 - i * 0.05})`,
                                    borderRadius: '50%',
                                    animation: `ringPulse 3s ease-out infinite ${i * 0.5}s`
                                }} />
                            ))}
                        </div>

                        {/* Title */}
                        <h1 style={{
                            fontSize: 26, fontWeight: 700, margin: '0 0 8px',
                            letterSpacing: 3, color: '#fff'
                        }}>
                            DCP-TWIN PRO
                        </h1>
                        <p style={{
                            fontSize: 10, fontWeight: 500,
                            color: 'rgba(255,255,255,0.6)',
                            margin: 0, letterSpacing: 3, textTransform: 'uppercase'
                        }}>
                            Secure Industrial Access
                        </p>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

                        {/* Username Input */}
                        <div style={{ position: 'relative' }}>
                            <div style={{
                                position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)',
                                color: focusedField === 'username' || username ? '#fff' : 'rgba(255,255,255,0.5)',
                                transition: 'color 0.3s', zIndex: 2, pointerEvents: 'none'
                            }}>
                                <User size={16} strokeWidth={1.5} />
                            </div>
                            <input
                                type="text"
                                placeholder="User ID"
                                value={username}
                                onChange={(e) => { setUsername(e.target.value); setError(''); }}
                                onFocus={() => setFocusedField('username')}
                                onBlur={() => setFocusedField(null)}
                                style={{
                                    width: '100%', height: 48, padding: '0 14px 0 42px',
                                    background: 'rgba(255,255,255,0.08)',
                                    border: `1px solid ${focusedField === 'username' ? 'rgba(255,255,255,0.4)' : 'rgba(255,255,255,0.15)'}`,
                                    borderRadius: 8,
                                    fontSize: 14, color: '#fff',
                                    outline: 'none', transition: 'all 0.3s',
                                    fontFamily: 'inherit'
                                }}
                            />
                        </div>

                        {/* Password Input */}
                        <div style={{ position: 'relative' }}>
                            <div style={{
                                position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)',
                                color: focusedField === 'password' || password ? '#fff' : 'rgba(255,255,255,0.5)',
                                transition: 'color 0.3s', zIndex: 2, pointerEvents: 'none'
                            }}>
                                <KeyRound size={16} strokeWidth={1.5} />
                            </div>
                            <input
                                type={showPassword ? 'text' : 'password'}
                                placeholder="Access Key"
                                value={password}
                                onChange={(e) => { setPassword(e.target.value); setError(''); }}
                                onFocus={() => setFocusedField('password')}
                                onBlur={() => setFocusedField(null)}
                                style={{
                                    width: '100%', height: 48, padding: '0 42px 0 42px',
                                    background: 'rgba(255,255,255,0.08)',
                                    border: `1px solid ${focusedField === 'password' ? 'rgba(255,255,255,0.4)' : 'rgba(255,255,255,0.15)'}`,
                                    borderRadius: 8,
                                    fontSize: 14, color: '#fff',
                                    outline: 'none', transition: 'all 0.3s',
                                    fontFamily: 'inherit'
                                }}
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                style={{
                                    position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                                    background: 'none', border: 'none', padding: 0, cursor: 'pointer',
                                    color: 'rgba(255,255,255,0.5)', transition: 'color 0.3s'
                                }}
                                onMouseEnter={e => e.currentTarget.style.color = '#fff'}
                                onMouseLeave={e => e.currentTarget.style.color = 'rgba(255,255,255,0.5)'}
                            >
                                {showPassword ? <EyeOff size={16} strokeWidth={1.5} /> : <Eye size={16} strokeWidth={1.5} />}
                            </button>
                        </div>

                        {/* Error Message */}
                        {error && (
                            <div style={{
                                display: 'flex', alignItems: 'center', gap: 8,
                                padding: '10px 14px',
                                background: 'rgba(239, 68, 68, 0.2)',
                                border: '1px solid rgba(239, 68, 68, 0.4)',
                                borderRadius: 8,
                                color: '#fca5a5', fontSize: 12,
                                animation: 'shake 0.4s ease'
                            }}>
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="12" cy="12" r="10" />
                                    <line x1="12" y1="8" x2="12" y2="12" />
                                    <line x1="12" y1="16" x2="12.01" y2="16" />
                                </svg>
                                {error}
                            </div>
                        )}

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={isLoading}
                            style={{
                                width: '100%', height: 46, marginTop: 6,
                                background: '#fff',
                                border: 'none', borderRadius: 8,
                                fontSize: 12, fontWeight: 600, letterSpacing: 1.5, textTransform: 'uppercase',
                                color: '#000', cursor: isLoading ? 'wait' : 'pointer',
                                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                                transition: 'all 0.3s',
                                opacity: isLoading ? 0.7 : 1,
                                fontFamily: 'inherit'
                            }}
                            onMouseEnter={e => { if (!isLoading) { e.currentTarget.style.opacity = '0.9'; } }}
                            onMouseLeave={e => { e.currentTarget.style.opacity = isLoading ? '0.7' : '1'; }}
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
                                    <span>Authenticating...</span>
                                </>
                            ) : (
                                <>
                                    <span>Authenticate</span>
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                        <line x1="5" y1="12" x2="19" y2="12" />
                                        <polyline points="12 5 19 12 12 19" />
                                    </svg>
                                </>
                            )}
                        </button>
                    </form>

                    {/* Demo Credentials */}
                    <div style={{
                        marginTop: 24, padding: '14px',
                        background: 'rgba(255,255,255,0.03)',
                        border: '1px dashed rgba(255,255,255,0.15)',
                        borderRadius: 8
                    }}>
                        <div style={{
                            fontSize: 9, fontWeight: 600,
                            color: 'rgba(255,255,255,0.5)',
                            textTransform: 'uppercase', letterSpacing: 2,
                            textAlign: 'center', marginBottom: 10
                        }}>
                            Demo Credentials
                        </div>
                        <div style={{ display: 'flex', gap: 8 }}>
                            <button
                                type="button"
                                onClick={() => fillCredentials('worker', 'dcp2026')}
                                style={{
                                    flex: 1, padding: '10px 12px',
                                    background: 'rgba(255,255,255,0.06)',
                                    border: '1px solid rgba(255,255,255,0.1)',
                                    borderRadius: 6, cursor: 'pointer',
                                    transition: 'all 0.3s',
                                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4
                                }}
                                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.12)'; }}
                                onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.06)'; }}
                            >
                                <span style={{
                                    fontSize: 8, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1,
                                    color: '#fff', padding: '2px 6px',
                                    background: 'rgba(255,255,255,0.15)', borderRadius: 3
                                }}>Operator</span>
                                <span style={{ fontSize: 9, fontFamily: "'Monaco', monospace", color: 'rgba(255,255,255,0.6)' }}>
                                    worker / dcp2026
                                </span>
                            </button>
                            <button
                                type="button"
                                onClick={() => fillCredentials('owner', 'admin')}
                                style={{
                                    flex: 1, padding: '10px 12px',
                                    background: 'rgba(255,255,255,0.06)',
                                    border: '1px solid rgba(255,255,255,0.1)',
                                    borderRadius: 6, cursor: 'pointer',
                                    transition: 'all 0.3s',
                                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4
                                }}
                                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.12)'; }}
                                onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.06)'; }}
                            >
                                <span style={{
                                    fontSize: 8, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1,
                                    color: '#fff', padding: '2px 6px',
                                    background: 'rgba(255,255,255,0.15)', borderRadius: 3
                                }}>Director</span>
                                <span style={{ fontSize: 9, fontFamily: "'Monaco', monospace", color: 'rgba(255,255,255,0.6)' }}>
                                    owner / admin
                                </span>
                            </button>
                        </div>
                    </div>

                    {/* Footer */}
                    <div style={{ textAlign: 'center', marginTop: 20 }}>
                        <p style={{
                            margin: 0, fontSize: 9, fontWeight: 500,
                            color: 'rgba(255,255,255,0.45)',
                            letterSpacing: 1.5, textTransform: 'uppercase'
                        }}>
                            Authorized Personnel Only
                        </p>
                        <p style={{
                            margin: '4px 0 0', fontSize: 8,
                            color: 'rgba(255,255,255,0.3)'
                        }}>
                            Access is logged and monitored
                        </p>
                    </div>
                </div>

                {/* System Status Pill */}
                <div style={{
                    display: 'flex', alignItems: 'center', gap: 6,
                    padding: '6px 14px',
                    background: 'rgba(0, 0, 0, 0.5)',
                    backdropFilter: 'blur(8px)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 16,
                    fontSize: 10, color: 'rgba(255,255,255,0.6)'
                }}>
                    <div style={{
                        width: 5, height: 5, borderRadius: '50%',
                        background: '#22c55e',
                        boxShadow: '0 0 6px rgba(34, 197, 94, 0.5)',
                        animation: 'pulse 2s infinite'
                    }} />
                    <span>System Online</span>
                    <span style={{ color: 'rgba(255,255,255,0.25)' }}>·</span>
                    <span style={{ fontFamily: "'Monaco', monospace", color: 'rgba(255,255,255,0.45)' }}>v2.4.1</span>
                </div>
            </div>
        </div>
    );
};
