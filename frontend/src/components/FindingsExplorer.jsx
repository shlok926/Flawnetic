import React, { useState } from 'react';
import { ShieldAlert, Bug, Sparkles, ExternalLink, Filter, FileText } from 'lucide-react';

export default function FindingsExplorer({ findings, pdfUrl }) {
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [filterModule, setFilterModule] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const filtered = findings.filter(f => {
    const matchSev = filterSeverity === 'ALL' || f.severity.toUpperCase() === filterSeverity;
    const matchMod = filterModule === 'ALL' || f.module.toLowerCase() === filterModule.toLowerCase();
    const matchSearch = f.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                        f.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchSev && matchMod && matchSearch;
  });

  return (
    <div className="glass-panel" style={{ padding: '28px' }}>
      
      {/* Header & Filter Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.3rem', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Bug color="#ef4444" /> Discovered Flaws & Vulnerabilities ({findings.length})
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Normalized findings with evidence and Claude AI remediation instructions.
          </p>
        </div>

        {pdfUrl && (
          <a 
            href={pdfUrl} 
            target="_blank" 
            rel="noopener noreferrer" 
            className="btn-primary" 
            style={{ background: 'linear-gradient(135deg, #10b981, #059669)', textDecoration: 'none' }}
          >
            <FileText size={16} /> Download Enterprise PDF Report
          </a>
        )}
      </div>

      {/* Filter Toolbar */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <input 
          type="text" 
          placeholder="Search findings..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ padding: '8px 14px', borderRadius: '8px', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-color)', color: 'white', minWidth: '220px' }}
        />

        <select 
          value={filterSeverity} 
          onChange={(e) => setFilterSeverity(e.target.value)}
          style={{ padding: '8px 14px', borderRadius: '8px', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-color)', color: 'white' }}
        >
          <option value="ALL">All Severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>

        <select 
          value={filterModule} 
          onChange={(e) => setFilterModule(e.target.value)}
          style={{ padding: '8px 14px', borderRadius: '8px', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-color)', color: 'white' }}
        >
          <option value="ALL">All Modules</option>
          <option value="functional">Functional</option>
          <option value="security">Security DAST</option>
          <option value="accessibility">Accessibility WCAG</option>
          <option value="usability">Usability & Performance</option>
          <option value="visual">Visual & Layout</option>
        </select>
      </div>

      {/* Findings List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {filtered.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No findings match selected filter.
          </div>
        ) : (
          filtered.map((item, idx) => {
            const sevClass = `badge-${item.severity.toLowerCase()}`;
            return (
              <div 
                key={item.id || idx}
                style={{
                  background: 'rgba(255,255,255,0.02)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '12px',
                  padding: '20px',
                  transition: 'all 0.2s'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span className={`badge ${sevClass}`}>{item.severity}</span>
                    <span className="badge badge-module">{item.module}</span>
                    <h4 style={{ fontSize: '1.05rem', fontWeight: '600' }}>{item.title}</h4>
                  </div>
                </div>

                <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '16px', lineHeight: '1.5' }}>
                  {item.description}
                </p>

                {/* AI Remediation Box */}
                {item.root_cause_hint && (
                  <div 
                    style={{
                      background: 'rgba(99, 102, 241, 0.08)',
                      border: '1px solid rgba(99, 102, 241, 0.25)',
                      borderRadius: '10px',
                      padding: '14px 16px',
                      fontSize: '0.85rem',
                      lineHeight: '1.5'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#a5b4fc', fontWeight: '600', marginBottom: '6px' }}>
                      <Sparkles size={16} /> Claude AI Remediation & Root Cause Analysis
                    </div>
                    <div style={{ color: '#e0e7ff', whiteSpace: 'pre-line' }}>
                      {item.root_cause_hint}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

    </div>
  );
}
