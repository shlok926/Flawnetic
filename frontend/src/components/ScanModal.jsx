import React, { useState } from 'react';
import { X, Globe, Sliders, Shield, Eye, Cpu, Accessibility, Gauge } from 'lucide-react';

export default function ScanModal({ isOpen, onClose, onStartScan }) {
  const [targetUrl, setTargetUrl] = useState('https://demo.testfire.net');
  const [maxPages, setMaxPages] = useState(25);
  const [maxDepth, setMaxDepth] = useState(3);
  const [modules, setModules] = useState({
    functional: true,
    security: true,
    accessibility: true,
    usability: true,
    visual: true
  });

  if (!isOpen) return null;

  const handleToggleModule = (key) => {
    setModules(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const activeModules = Object.keys(modules).filter(k => modules[k]);
    onStartScan({ targetUrl, maxPages, maxDepth, modules: activeModules });
    onClose();
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '600px', padding: '32px', position: 'relative' }}>
        
        <button onClick={onClose} style={{ position: 'absolute', top: '20px', right: '20px', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
          <X size={20} />
        </button>

        <h2 style={{ fontSize: '1.4rem', fontWeight: '700', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Globe color="#6366f1" /> Launch Autonomous QA Audit
        </h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '24px' }}>
          Enter target URL. Flawnetic AI will crawl, fuzz, and audit across 5 dimensions.
        </p>

        <form onSubmit={handleSubmit}>
          {/* Target URL Input */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: '600', marginBottom: '8px', color: 'var(--text-muted)' }}>Target Website URL</label>
            <input 
              type="url"
              required
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              placeholder="https://example.com"
              style={{ width: '100%', padding: '12px 16px', borderRadius: '10px', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-color)', color: 'white', outline: 'none' }}
            />
          </div>

          {/* Crawl Limits */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: '600', marginBottom: '8px', color: 'var(--text-muted)' }}>Max Crawl Pages</label>
              <input 
                type="number"
                min="1"
                max="100"
                value={maxPages}
                onChange={(e) => setMaxPages(parseInt(e.target.value))}
                style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-color)', color: 'white' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: '600', marginBottom: '8px', color: 'var(--text-muted)' }}>Max Depth Limit</label>
              <input 
                type="number"
                min="1"
                max="10"
                value={maxDepth}
                onChange={(e) => setMaxDepth(parseInt(e.target.value))}
                style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-color)', color: 'white' }}
              />
            </div>
          </div>

          {/* Module Selectors */}
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: '600', marginBottom: '12px', color: 'var(--text-muted)' }}>Active Scan Engines (5-in-1)</label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '28px' }}>
            
            {[
              { id: 'functional', label: 'Functional Fuzzing', icon: Cpu, color: '#6366f1' },
              { id: 'security', label: 'OWASP ZAP Security DAST', icon: Shield, color: '#ef4444' },
              { id: 'accessibility', label: 'axe WCAG 2.1 AA', icon: Accessibility, color: '#10b981' },
              { id: 'usability', label: 'Usability & Performance', icon: Gauge, color: '#f59e0b' },
              { id: 'visual', label: 'Cross-Browser Layout', icon: Eye, color: '#8b5cf6' },
            ].map((m) => {
              const Icon = m.icon;
              const active = modules[m.id];
              return (
                <div 
                  key={m.id}
                  onClick={() => handleToggleModule(m.id)}
                  style={{
                    padding: '12px',
                    borderRadius: '10px',
                    border: `1px solid ${active ? m.color : 'var(--border-color)'}`,
                    background: active ? `${m.color}15` : 'rgba(255,255,255,0.02)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    transition: 'all 0.2s'
                  }}
                >
                  <Icon size={18} color={active ? m.color : 'var(--text-dim)'} />
                  <span style={{ fontSize: '0.85rem', fontWeight: active ? '600' : '400', color: active ? 'white' : 'var(--text-muted)' }}>{m.label}</span>
                </div>
              );
            })}
          </div>

          <button type="submit" className="btn-primary" style={{ width: '100%', justifyContent: 'center', padding: '14px' }}>
            Start Autonomous Scan Pass
          </button>
        </form>
      </div>
    </div>
  );
}
