import React, { useState } from 'react';

const ChoiceButton = ({ children, onClick, variant = 'default', subtext, disabled = false }) => {
    const [isHovered, setIsHovered] = useState(false);
    const [isPressed, setIsPressed] = useState(false);

    const baseStyle = {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px 24px',
        margin: '8px 0',
        borderRadius: '12px',
        border: '2px solid transparent',
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.3s ease',
        width: '100%',
        fontFamily: 'inherit',
        opacity: disabled ? 0.5 : 1,
        position: 'relative',
        overflow: 'hidden',
    };

    const variantStyles = {
        default: {
            background: isHovered ? 'var(--color-primary, #6c63ff)' : 'var(--color-surface, #1e1e2e)',
            color: isHovered ? '#fff' : 'var(--color-text, #e0e0e0)',
            borderColor: isHovered ? 'var(--color-primary, #6c63ff)' : 'var(--color-border, #333)',
            transform: isPressed ? 'scale(0.97)' : isHovered ? 'translateY(-2px)' : 'none',
            boxShadow: isHovered ? '0 6px 20px rgba(108,99,255,0.3)' : '0 2px 8px rgba(0,0,0,0.2)',
        },
        safe: {
            background: isHovered ? '#2ecc71' : 'var(--color-surface, #1e1e2e)',
            color: isHovered ? '#fff' : '#2ecc71',
            borderColor: '#2ecc71',
            transform: isPressed ? 'scale(0.97)' : isHovered ? 'translateY(-2px)' : 'none',
            boxShadow: isHovered ? '0 6px 20px rgba(46,204,113,0.3)' : '0 2px 8px rgba(0,0,0,0.2)',
        },
        risky: {
            background: isHovered ? '#e74c3c' : 'var(--color-surface, #1e1e2e)',
            color: isHovered ? '#fff' : '#e74c3c',
            borderColor: '#e74c3c',
            transform: isPressed ? 'scale(0.97)' : isHovered ? 'translateY(-2px)' : 'none',
            boxShadow: isHovered ? '0 6px 20px rgba(231,76,60,0.3)' : '0 2px 8px rgba(0,0,0,0.2)',
        },
    };

    const style = { ...baseStyle, ...(variantStyles[variant] || variantStyles.default) };

    return (
        <button
            style={style}
            onClick={disabled ? undefined : onClick}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => { setIsHovered(false); setIsPressed(false); }}
            onMouseDown={() => setIsPressed(true)}
            onMouseUp={() => setIsPressed(false)}
            disabled={disabled}
        >
            <span style={{ fontSize: '1rem', fontWeight: 600 }}>{children}</span>
            {subtext && <span style={{ fontSize: '0.8rem', opacity: 0.7, marginTop: 4 }}>{subtext}</span>}
        </button>
    );
};

export default ChoiceButton;
