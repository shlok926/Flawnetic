import React from 'react';
import { ShieldCheck, Play, Activity, FileText } from 'lucide-react';

export default function Navbar({ onNewScan, totalScans }) {
  return (
    <header className="glass-panel" style={{ borderRadius: '0 0 16px 16px', padding: '16px 32px', marginBottom: '32px' }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        
        {/* Brand Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ background: 'linear-gradient(135deg, #6366f1, #06b6d4)', padding: '10px', borderRadius: '12px', display: 'flex' }}>
            <ShieldCheck size={26} color="white" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: '800', letterSpacing: '-0.5px' }}>
              Flawnetic <span style={{ color: '#06b6d4', fontSize: '0.9rem', fontWeight: '600', padding: '2px 8px', borderRadius: '6px', background: 'rgba(6,182,212,0.15)' }}>AI Platform</span>
            </h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Autonomous End-to-End Website QA & Security Audit</p>
          </div>
        </div>

        {/* Quick Stats & Action */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(255,255,255,0.03)', padding: '8px 16px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            <Activity size={18} color="#10b981" />
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Active Scans: <strong style={{ color: 'white' }}>{totalScans}</strong></span>
          </div>

          <button className="btn-primary" onClick={onNewScan}>
            <Play size={16} /> New Autonomous Scan
          </button>
        </div>
      </div>
    </header>
  );
}
