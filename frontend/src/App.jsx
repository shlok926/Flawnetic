import React, { useState } from 'react';
import Navbar from './components/Navbar';
import ScanModal from './components/ScanModal';
import ScanTracker from './components/ScanTracker';
import FindingsExplorer from './components/FindingsExplorer';
import { ShieldCheck, Bug, Cpu, AlertTriangle, Layers } from 'lucide-react';

export default function App() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentScan, setCurrentScan] = useState({
    id: 'demo-scan-1',
    targetUrl: 'https://demo.testfire.net',
    status: 'done',
    pdfUrl: 'https://localhost:9000/flawnetic/reports/sample.pdf'
  });

  const [findings, setFindings] = useState([
    {
      id: 'f-1',
      module: 'security',
      title: 'Possible SQL Injection Vulnerability',
      description: 'Form input at https://demo.testfire.net/login.jsp returned unhandled database syntax error when injected with SQL fuzzing payload.',
      severity: 'CRITICAL',
      root_cause_hint: '**Root Cause:** Direct string concatenation in SQL queries without parameterized statement binding.\n**Remediation:** Replace dynamic SQL query concatenation with PreparedStatement placeholders.'
    },
    {
      id: 'f-2',
      module: 'security',
      title: 'Missing Content Security Policy (CSP)',
      description: 'Content-Security-Policy header is missing on HTTP responses, exposing site to cross-site scripting (XSS) attacks.',
      severity: 'HIGH',
      root_cause_hint: '**Root Cause:** Web server HTTP response header configuration is missing CSP directive.\n**Remediation:** Add `Content-Security-Policy: default-src \'self\';` header in web server configuration.'
    },
    {
      id: 'f-3',
      module: 'accessibility',
      title: 'WCAG Violation: Form Input Missing Associated Label',
      description: 'Search field on main header lacks an explicit `<label>` or `aria-label` attribute.',
      severity: 'MEDIUM',
      root_cause_hint: '**Root Cause:** Input element lacks matching label ID or ARIA label.\n**Remediation:** Add `aria-label="Search"` or `<label for="...">` element.'
    },
    {
      id: 'f-4',
      module: 'usability',
      title: 'Uncaught Browser Console Errors',
      description: 'Page emitted 3 JavaScript console errors during load: "TypeError: Cannot read properties of undefined".',
      severity: 'LOW',
      root_cause_hint: '**Root Cause:** Accessing properties on null/undefined object during page initialization.\n**Remediation:** Add optional chaining (`object?.property`) or null checks before dereferencing.'
    }
  ]);

  const handleStartScan = (scanConfig) => {
    setCurrentScan({
      id: `scan-${Date.now()}`,
      targetUrl: scanConfig.targetUrl,
      status: 'crawling',
      pdfUrl: null
    });

    // Simulate progress pipeline
    setTimeout(() => {
      setCurrentScan(prev => ({ ...prev, status: 'testing' }));
    }, 3000);

    setTimeout(() => {
      setCurrentScan(prev => ({ 
        ...prev, 
        status: 'done',
        pdfUrl: 'http://localhost:9000/flawnetic/reports/report_sample.pdf' 
      }));
    }, 7000);
  };

  return (
    <div style={{ minHeight: '100vh', paddingBottom: '60px', position: 'relative' }}>
      <div className="grain" />
      <Navbar onNewScan={() => setIsModalOpen(true)} totalScans={1} />

      <main style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 24px' }}>
        
        {/* Metric Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginBottom: '32px' }}>
          
          <div className="glass-panel" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600' }}>TOTAL FINDINGS</span>
              <Bug size={20} color="#6366f1" />
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: '800' }}>{findings.length}</div>
          </div>

          <div className="glass-panel" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600' }}>CRITICAL / HIGH</span>
              <AlertTriangle size={20} color="#ef4444" />
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#ef4444' }}>
              {findings.filter(f => f.severity === 'CRITICAL' || f.severity === 'HIGH').length}
            </div>
          </div>

          <div className="glass-panel" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600' }}>ACTIVE ENGINES</span>
              <Cpu size={20} color="#10b981" />
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#10b981' }}>5 / 5</div>
          </div>

          <div className="glass-panel" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600' }}>AUDIT COMPLIANCE</span>
              <ShieldCheck size={20} color="#06b6d4" />
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#06b6d4' }}>82%</div>
          </div>

        </div>

        {/* Live Scan Tracker */}
        <ScanTracker currentScan={currentScan} />

        {/* Findings Explorer */}
        <FindingsExplorer findings={findings} pdfUrl={currentScan?.pdfUrl} />

      </main>

      <ScanModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onStartScan={handleStartScan} 
      />
    </div>
  );
}
