import { useState } from 'react';
import GradientBlinds from './GradientBlinds';
import './LoginPage.css';

const LoginPage = ({ onLogin }) => {
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        rememberMe: false
    });
    const [isLoading, setIsLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [errors, setErrors] = useState({});

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
        // Clear error when user starts typing
        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
    };

    const validateForm = () => {
        const newErrors = {};
        if (!formData.email) {
            newErrors.email = 'Email is required';
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
            newErrors.email = 'Please enter a valid email';
        }
        if (!formData.password) {
            newErrors.password = 'Password is required';
        } else if (formData.password.length < 6) {
            newErrors.password = 'Password must be at least 6 characters';
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!validateForm()) return;

        setIsLoading(true);
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1500));
        setIsLoading(false);

        if (onLogin) {
            onLogin(formData);
        }
    };

    return (
        <div className="login-page">
            {/* Animated Background */}
            <div className="login-background">
                <GradientBlinds
                    gradientColors={['#0a0a1a', '#1a1a3e', '#2d1b69', '#4a1c6b', '#6b21a8']}
                    angle={-15}
                    noise={0.15}
                    blindCount={14}
                    blindMinWidth={80}
                    spotlightRadius={0.6}
                    spotlightSoftness={1.2}
                    spotlightOpacity={0.8}
                    mouseDampening={0.12}
                    distortAmount={0.5}
                    shineDirection="left"
                    mixBlendMode="normal"
                />
            </div>

            {/* Floating Particles */}
            <div className="particles">
                {[...Array(20)].map((_, i) => (
                    <div
                        key={i}
                        className="particle"
                        style={{
                            '--delay': `${Math.random() * 5}s`,
                            '--duration': `${15 + Math.random() * 10}s`,
                            '--x-start': `${Math.random() * 100}%`,
                            '--x-end': `${Math.random() * 100}%`,
                            '--size': `${2 + Math.random() * 4}px`
                        }}
                    />
                ))}
            </div>

            {/* Login Card */}
            <div className="login-container">
                <div className="login-card">
                    {/* Glassmorphism glow effect */}
                    <div className="card-glow"></div>

                    {/* Logo & Header */}
                    <div className="login-header">
                        <div className="logo-container">
                            <div className="logo-icon">
                                <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <circle cx="20" cy="20" r="18" stroke="url(#logoGradient)" strokeWidth="2" />
                                    <path d="M12 20L18 26L28 14" stroke="url(#logoGradient)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                                    <defs>
                                        <linearGradient id="logoGradient" x1="0" y1="0" x2="40" y2="40">
                                            <stop offset="0%" stopColor="#a855f7" />
                                            <stop offset="100%" stopColor="#6366f1" />
                                        </linearGradient>
                                    </defs>
                                </svg>
                            </div>
                            <div className="logo-rings">
                                <div className="ring ring-1"></div>
                                <div className="ring ring-2"></div>
                                <div className="ring ring-3"></div>
                            </div>
                        </div>
                        <h1 className="login-title">Digital Twin</h1>
                        <p className="login-subtitle">Industrial Control System</p>
                    </div>

                    {/* Login Form */}
                    <form className="login-form" onSubmit={handleSubmit}>
                        {/* Email Field */}
                        <div className={`form-group ${errors.email ? 'has-error' : ''} ${formData.email ? 'has-value' : ''}`}>
                            <div className="input-wrapper">
                                <span className="input-icon">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                                        <polyline points="22,6 12,13 2,6" />
                                    </svg>
                                </span>
                                <input
                                    type="email"
                                    id="email"
                                    name="email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    placeholder=" "
                                    autoComplete="email"
                                />
                                <label htmlFor="email">Email Address</label>
                                <div className="input-highlight"></div>
                            </div>
                            {errors.email && <span className="error-message">{errors.email}</span>}
                        </div>

                        {/* Password Field */}
                        <div className={`form-group ${errors.password ? 'has-error' : ''} ${formData.password ? 'has-value' : ''}`}>
                            <div className="input-wrapper">
                                <span className="input-icon">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                                        <path d="M7 11V7a5 5 0 0110 0v4" />
                                    </svg>
                                </span>
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    id="password"
                                    name="password"
                                    value={formData.password}
                                    onChange={handleChange}
                                    placeholder=" "
                                    autoComplete="current-password"
                                />
                                <label htmlFor="password">Password</label>
                                <button
                                    type="button"
                                    className="password-toggle"
                                    onClick={() => setShowPassword(!showPassword)}
                                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                                >
                                    {showPassword ? (
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24" />
                                            <line x1="1" y1="1" x2="23" y2="23" />
                                        </svg>
                                    ) : (
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                                            <circle cx="12" cy="12" r="3" />
                                        </svg>
                                    )}
                                </button>
                                <div className="input-highlight"></div>
                            </div>
                            {errors.password && <span className="error-message">{errors.password}</span>}
                        </div>

                        {/* Remember & Forgot */}
                        <div className="form-options">
                            <label className="checkbox-wrapper">
                                <input
                                    type="checkbox"
                                    name="rememberMe"
                                    checked={formData.rememberMe}
                                    onChange={handleChange}
                                />
                                <span className="checkmark"></span>
                                <span className="checkbox-label">Remember me</span>
                            </label>
                            <a href="#" className="forgot-link">Forgot password?</a>
                        </div>

                        {/* Submit Button */}
                        <button
                            type="submit"
                            className={`login-button ${isLoading ? 'loading' : ''}`}
                            disabled={isLoading}
                        >
                            <span className="button-content">
                                {isLoading ? (
                                    <>
                                        <span className="spinner"></span>
                                        <span>Authenticating...</span>
                                    </>
                                ) : (
                                    <>
                                        <span>Access System</span>
                                        <svg className="arrow-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <line x1="5" y1="12" x2="19" y2="12" />
                                            <polyline points="12 5 19 12 12 19" />
                                        </svg>
                                    </>
                                )}
                            </span>
                            <div className="button-glow"></div>
                        </button>
                    </form>

                    {/* Divider */}
                    <div className="divider">
                        <span>or continue with</span>
                    </div>

                    {/* Social Login */}
                    <div className="social-login">
                        <button className="social-button" type="button" aria-label="Login with Google">
                            <svg viewBox="0 0 24 24">
                                <path fill="#EA4335" d="M5.26620003,9.76452941 C6.19878754,6.93863203 8.85444915,4.90909091 12,4.90909091 C13.6909091,4.90909091 15.2181818,5.50909091 16.4181818,6.49090909 L19.9090909,3 C17.7818182,1.14545455 15.0545455,0 12,0 C7.27006974,0 3.1977497,2.69829785 1.23999023,6.65002441 L5.26620003,9.76452941 Z" />
                                <path fill="#34A853" d="M16.0407269,18.0125889 C14.9509167,18.7163016 13.5660892,19.0909091 12,19.0909091 C8.86648613,19.0909091 6.21911939,17.076871 5.27698177,14.2678769 L1.23746264,17.3349879 C3.19279051,21.2936293 7.26500293,24 12,24 C14.9328362,24 17.7353462,22.9573905 19.834192,20.9995801 L16.0407269,18.0125889 Z" />
                                <path fill="#4A90E2" d="M19.834192,20.9995801 C22.0291676,18.9520994 23.4545455,15.903663 23.4545455,12 C23.4545455,11.2909091 23.3454545,10.5272727 23.1818182,9.81818182 L12,9.81818182 L12,14.4545455 L18.4363636,14.4545455 C18.1187732,16.013626 17.2662994,17.2212117 16.0407269,18.0125889 L19.834192,20.9995801 Z" />
                                <path fill="#FBBC05" d="M5.27698177,14.2678769 C5.03832634,13.556323 4.90909091,12.7937589 4.90909091,12 C4.90909091,11.2182781 5.03443647,10.4668121 5.26620003,9.76452941 L1.23999023,6.65002441 C0.43658717,8.26043162 0,10.0753848 0,12 C0,13.9195484 0.444780743,15.7## Z" />
                            </svg>
                        </button>
                        <button className="social-button" type="button" aria-label="Login with Microsoft">
                            <svg viewBox="0 0 24 24">
                                <path fill="#F25022" d="M0 0h11.377v11.377H0z" />
                                <path fill="#00A4EF" d="M0 12.623h11.377V24H0z" />
                                <path fill="#7FBA00" d="M12.623 0H24v11.377H12.623z" />
                                <path fill="#FFB900" d="M12.623 12.623H24V24H12.623z" />
                            </svg>
                        </button>
                        <button className="social-button" type="button" aria-label="Login with SSO">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4" />
                                <polyline points="10 17 15 12 10 7" />
                                <line x1="15" y1="12" x2="3" y2="12" />
                            </svg>
                        </button>
                    </div>

                    {/* Footer */}
                    <div className="login-footer">
                        <p>Don't have an account? <a href="#">Request Access</a></p>
                    </div>
                </div>

                {/* System Status */}
                <div className="system-status">
                    <div className="status-indicator online"></div>
                    <span>System Online</span>
                    <span className="status-separator">•</span>
                    <span className="status-version">v2.4.1</span>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
