import React from 'react';
import { Loader2, CheckCircle2, AlertTriangle, FileCheck } from 'lucide-react';

export default function ScanTracker({ currentScan }) {
  if (!currentScan) return null;

  const steps = ['crawling', 'testing', 'reporting', 'done'];
  const statusIndex = steps.indexOf(currentScan.status);
  const isDone = currentScan.status === 'done';
  const isFailed = currentScan.status === 'failed';

  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text-muted)' }}>Live Audit Progress</span>
          <h3 style={{ fontSize: '1.2rem', fontWeight: '700', marginTop: '2px' }}>{currentScan.targetUrl}</h3>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isDone ? (
            <span className="badge badge-low" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <CheckCircle2 size={14} /> Audit Completed
            </span>
          ) : isFailed ? (
            <span className="badge badge-high" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <AlertTriangle size={14} /> Scan Failed
            </span>
          ) : (
            <span className="badge badge-medium pulse" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Loader2 size={14} className="spin" /> Executing {currentScan.status}...
            </span>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div style={{ height: '8px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', overflow: 'hidden', marginBottom: '20px' }}>
        <div 
          style={{ 
            height: '100%', 
            width: isDone ? '100%' : `${Math.max(15, ((statusIndex + 1) / steps.length) * 100)}%`,
            background: isDone ? 'linear-gradient(90deg, #10b981, #06b6d4)' : 'linear-gradient(90deg, #6366f1, #06b6d4)',
            transition: 'width 0.4s ease'
          }} 
        />
      </div>

      {/* Stage indicators */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
        {steps.map((stage, idx) => {
          const active = idx <= statusIndex || isDone;
          return (
            <div key={stage} style={{ textAlign: 'center', opacity: active ? 1 : 0.4 }}>
              <span style={{ fontSize: '0.75rem', fontWeight: '600', textTransform: 'capitalize', color: active ? 'white' : 'var(--text-muted)' }}>
                {stage === 'done' ? 'Report Ready' : stage}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
