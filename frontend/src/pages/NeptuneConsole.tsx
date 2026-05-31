import { useEffect, useMemo } from 'react';
import '../styles/alerts-futuristic.css';
import { useAlertUIStore } from '../store/useAlertUIStore';
import { useSystemStore } from '../store/useSystemStore';
import type { Severity, AlertState, Alert, Ioc, TimelineStep, Enrichment } from '../store/types';

const ALERTS: Alert[] = [
  {
    id: 'ALT-20240528-001',
    severity: 'CRITICAL',
    title: 'Credential Dumping via LSASS Process Access',
    source: 'CrowdStrike',
    entity: 'WIN-PROD-001',
    tactic: 'Credential Access',
    technique: 'T1003.001 — LSASS Memory',
    detected: '21:43:12',
    state: 'IN_PROGRESS',
    analyst: 'A. Reed',
    correlations: 3,
    risk: 92,
    desc: 'Falcon sensor detected LSASS memory read by suspicious process mimikatz.exe. Process spawned under SYSTEM context from non-standard parent cmd.exe.',
    iocs: [
      { type: 'SHA256', val: 'e3b0c44298fc1c14', conf: 95 },
      { type: 'PROCESS', val: 'mimikatz.exe', conf: 98 },
      { type: 'HOST', val: 'WIN-PROD-001', conf: 100 },
    ],
    timeline: [
      { t: '21:43:12', txt: 'Falcon EDR detected LSASS memory access', act: true },
      { t: '21:43:15', txt: 'Process tree captured — parent: cmd.exe' },
      { t: '21:44:02', txt: 'Assigned to A. Reed for triage' },
      { t: '21:45:30', txt: 'Investigation in progress — awaiting memory dump' },
    ],
    enrichment: { abuseipdb: null, virustotal: '5/72 detections', greynoise: 'Not observed' },
  },
  {
    id: 'ALT-20240528-002',
    severity: 'CRITICAL',
    title: 'Shadow Copy Deletion — Ransomware Precursor Activity',
    source: 'CrowdStrike',
    entity: 'FILE-SRV-03',
    tactic: 'Impact',
    technique: 'T1490 — Inhibit System Recovery',
    detected: '21:38:55',
    state: 'ESCALATED',
    analyst: 'J. Chen',
    correlations: 0,
    risk: 96,
    desc: 'vssadmin.exe executed with delete shadows parameter. Consistent with pre-encryption stage of ransomware deployment.',
    iocs: [
      { type: 'CMD', val: 'vssadmin delete shadows /all', conf: 99 },
      { type: 'PROC', val: 'vssadmin.exe (SYSTEM)', conf: 97 },
    ],
    timeline: [
      { t: '21:38:55', txt: 'Shadow copy deletion command detected', act: true },
      { t: '21:39:01', txt: 'Alert escalated — potential ransomware' },
      { t: '21:39:20', txt: 'J. Chen investigating — host isolated' },
    ],
    enrichment: { abuseipdb: null, virustotal: null, greynoise: null },
  },
  {
    id: 'ALT-20240528-003',
    severity: 'HIGH',
    title: 'Lateral Movement via Pass-the-Hash Attack',
    source: 'Defender ATP',
    entity: 'WIN-DEV-027',
    tactic: 'Lateral Movement',
    technique: 'T1550.002 — Pass the Hash',
    detected: '21:35:41',
    state: 'ACKNOWLEDGED',
    analyst: 'A. Reed',
    correlations: 2,
    risk: 78,
    desc: 'Authentication event from non-interactive logon using NTLM hash. Source host WIN-DEV-027 is not a domain admin system.',
    iocs: [
      { type: 'IP', val: '10.20.1.27', conf: 85 },
      { type: 'ACCOUNT', val: 'svc-backup\\SYSTEM', conf: 90 },
    ],
    timeline: [
      { t: '21:35:41', txt: 'NTLM hash authentication detected', act: true },
      { t: '21:36:10', txt: 'Correlated with ALT-001 credential dump' },
      { t: '21:37:00', txt: 'Acknowledged by A. Reed' },
    ],
    enrichment: { abuseipdb: 'Not listed', virustotal: null, greynoise: 'Not observed' },
  },
  {
    id: 'ALT-20240528-004',
    severity: 'HIGH',
    title: 'Suspicious PowerShell Encoded Command Execution',
    source: 'SIEM',
    entity: 'WIN-HR-012',
    tactic: 'Execution',
    technique: 'T1059.001 — PowerShell',
    detected: '21:30:22',
    state: 'NEW',
    analyst: null,
    correlations: 0,
    risk: 71,
    desc: 'Encoded base64 PowerShell command executed by non-admin user. Command decodes to a web download cradle targeting an external IP.',
    iocs: [
      { type: 'URL', val: 'hxxp://194.165.16.11/stage2.ps1', conf: 88 },
      { type: 'CMD', val: 'powershell -enc JABz...', conf: 80 },
    ],
    timeline: [
      { t: '21:30:22', txt: 'Encoded PS execution detected', act: true },
      { t: '21:30:25', txt: 'Network connection attempt to 194.165.16.11' },
    ],
    enrichment: { abuseipdb: 'Reported 47 times', virustotal: '12/72 flagged', greynoise: 'Malicious' },
  },
  {
    id: 'ALT-20240528-005',
    severity: 'HIGH',
    title: 'C2 Beacon — Outbound to Known Malicious Infrastructure',
    source: 'NDR',
    entity: 'WIN-PROD-044',
    tactic: 'Command & Control',
    technique: 'T1071.001 — Web Protocols',
    detected: '21:28:17',
    state: 'NEW',
    analyst: null,
    correlations: 1,
    risk: 83,
    desc: 'Periodic HTTP beaconing to 194.165.16.11 every 60 seconds. Consistent with Cobalt Strike beacon profile. Jitter pattern matches known C2 framework.',
    iocs: [
      { type: 'IP', val: '194.165.16.11', conf: 94 },
      { type: 'DOMAIN', val: 'update-svc.net', conf: 91 },
      { type: 'PORT', val: '443/TCP', conf: 75 },
    ],
    timeline: [
      { t: '21:28:17', txt: 'First beacon detected', act: true },
      { t: '21:29:17', txt: 'Second beacon — 60s interval confirmed' },
      { t: '21:30:17', txt: 'Third beacon — C2 profile match' },
    ],
    enrichment: { abuseipdb: 'Reported 214 times', virustotal: '48/72 flagged', greynoise: 'Malicious — Cobalt Strike' },
  },
];

type SortKey = 'severity' | 'id' | 'entity' | 'detected';

function formatStateLabel(state: AlertState) {
  return state.replace('_', ' ');
}

function formatAnalyst(analyst: string | null) {
  if (!analyst) return 'Unassigned';
  const parts = analyst.split(' ');
  return parts.length > 1 ? parts[1] : analyst;
}

export default function NeptuneConsole() {
  // Subscribe to UI state from the centralized store
  const selectedId = useAlertUIStore((state) => state.selectedAlertId);
  const selectedRows = useAlertUIStore((state) => state.selectedRows);
  const sortKey = useAlertUIStore((state) => state.sortKey);
  const sortDir = useAlertUIStore((state) => state.sortDir);
  const searchQuery = useAlertUIStore((state) => state.searchQuery);
  const stateFilter = useAlertUIStore((state) => state.stateFilter);
  const sevFilter = useAlertUIStore((state) => state.sevFilter);

  // Subscribe to UI actions
  const setSelectedId = useAlertUIStore((state) => state.setSelectedAlertId);
  const toggleRow = useAlertUIStore((state) => state.toggleSelectedRow);
  const setSelectedRows = useAlertUIStore((state) => state.setSelectedRows);
  const setSevFilter = useAlertUIStore((state) => state.setSevFilter);
  const setStateFilter = useAlertUIStore((state) => state.setStateFilter);
  const setSearchQuery = useAlertUIStore((state) => state.setSearchQuery);

  // Subscribe to system metrics
  const rate = useSystemStore((state) => state.eventRate);
  const setEventRate = useSystemStore((state) => state.setEventRate);

  // Update event rate every 3 seconds
  useEffect(() => {
    const interval = window.setInterval(
      () => setEventRate(Math.floor(Math.random() * 200 + 400)),
      3000
    );
    return () => window.clearInterval(interval);
  }, [setEventRate]);

  const filteredAlerts = useMemo(() => {
    const term = searchQuery.toLowerCase();
    return ALERTS.filter((alert) => {
      const matchesSeverity = sevFilter === 'ALL' || alert.severity === sevFilter;
      const matchesState = !stateFilter || alert.state === stateFilter;
      const matchesSearch =
        !term ||
        alert.title.toLowerCase().includes(term) ||
        alert.id.toLowerCase().includes(term) ||
        alert.entity.toLowerCase().includes(term) ||
        alert.source.toLowerCase().includes(term) ||
        alert.tactic.toLowerCase().includes(term);
      return matchesSeverity && matchesState && matchesSearch;
    }).sort((a, b) => {
      if (sortKey === 'severity') return (['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'].indexOf(a.severity) - ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'].indexOf(b.severity)) * sortDir;
      if (sortKey === 'id') return a.id.localeCompare(b.id) * sortDir;
      if (sortKey === 'entity') return a.entity.localeCompare(b.entity) * sortDir;
      return sortDir === 1 ? a.detected.localeCompare(b.detected) : b.detected.localeCompare(a.detected);
    });
  }, [searchQuery, stateFilter, sevFilter, sortKey, sortDir]);

  const counts = useMemo(() => {
    const result: Record<'ALL' | Severity, number> = { ALL: 0, CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, INFO: 0 };
    ALERTS.forEach((alert) => {
      result.ALL += 1;
      result[alert.severity] += 1;
    });
    return result;
  }, []);

  const selectedAlert = useMemo(() => ALERTS.find((alert) => alert.id === selectedId) ?? null, [selectedId]);
  const criticalOpen = ALERTS.filter((alert) => alert.severity === 'CRITICAL' && alert.state !== 'CLOSED' && alert.state !== 'FALSE_POSITIVE').length;
  const openAlerts = ALERTS.filter((alert) => alert.state !== 'CLOSED' && alert.state !== 'FALSE_POSITIVE').length;

  // Row selection handlers using the store
  const handleToggleRow = (id: string, checked: boolean) => {
    if (checked) {
      toggleRow(id);
    } else {
      toggleRow(id);
    }
  };

  const handleToggleAll = (checked: boolean) => {
    if (!checked) {
      setSelectedRows(new Set());
      return;
    }
    setSelectedRows(new Set(filteredAlerts.map((alert) => alert.id)));
  };

  const analystData: Record<string, { initials: string; color: string }> = {
    'A. Reed': { initials: 'AR', color: '#7c3aed' },
    'J. Chen': { initials: 'JC', color: '#2563eb' },
    'M. Okafor': { initials: 'MO', color: '#059669' },
    'S. Patel': { initials: 'SP', color: '#b45309' },
  };

  const selectedCount = selectedRows.size;
  const selectAllChecked = filteredAlerts.length > 0 && selectedCount === filteredAlerts.length;

  return (
    <div className="shell">
      <header>
        <div className="hd-brand">
          <div className="hd-logo"><i className="ti ti-shield-bolt" /></div>
          <span className="hd-name">SOCopilot</span>
          <span className="hd-sep">/</span>
          <span className="hd-org">Acme Corp</span>
        </div>
        <nav className="hd-nav">
          <button type="button" className="hn-btn"><i className="ti ti-layout-dashboard" /> Dashboard</button>
          <button type="button" className="hn-btn active"><i className="ti ti-bell-ringing" /> Alerts</button>
          <button type="button" className="hn-btn"><i className="ti ti-folder-open" /> Cases</button>
          <button type="button" className="hn-btn"><i className="ti ti-search" /> Investigate</button>
        </nav>
        <div className="hd-stats">
          <div className="hstat"><div className="hs-val r">{openAlerts}</div><div className="hs-lbl">Open Alerts</div></div>
          <div className="hd-vsep" />
          <div className="hstat"><div className="hs-val r">{criticalOpen}</div><div className="hs-lbl">Critical</div></div>
          <div className="hd-vsep" />
          <div className="hstat"><div className="hs-val g">99.8%</div><div className="hs-lbl">Pipeline Health</div></div>
          <div className="hd-vsep" />
          <div className="hstat"><div className="hs-val">{rate}</div><div className="hs-lbl">Events / sec</div></div>
        </div>
        <div className="hd-right">
          <div className="live-badge"><div className="live-dot" /><span className="live-txt">LIVE</span></div>
          <button type="button" className="hd-btn has-tip" data-tip="Notifications"><i className="ti ti-bell" /><span className="nb" /></button>
          <button type="button" className="hd-btn has-tip" data-tip="Settings"><i className="ti ti-settings" /></button>
          <div className="avatar">JS</div>
        </div>
      </header>

      <div className="body">
        <nav className="sidebar">
          <button type="button" className="sb-btn" title="Dashboard"><i className="ti ti-layout-dashboard" /><span className="tt">Dashboard</span></button>
          <button type="button" className="sb-btn active" title="Alert Queue"><i className="ti ti-bell-ringing" /><span className="tt">Alert Queue</span></button>
          <button type="button" className="sb-btn" title="Cases"><i className="ti ti-folder-open" /><span className="tt">Cases</span></button>
          <div className="sb-sep" />
          <button type="button" className="sb-btn" title="Investigate"><i className="ti ti-timeline-event" /><span className="tt">Investigate</span></button>
          <button type="button" className="sb-btn" title="Telemetry"><i className="ti ti-chart-line" /><span className="tt">Telemetry</span></button>
          <button type="button" className="sb-btn" title="AI Copilot"><i className="ti ti-robot" /><span className="tt">AI Copilot</span></button>
          <div className="sb-sep" />
          <button type="button" className="sb-btn" title="Analysts"><i className="ti ti-users" /><span className="tt">Analysts</span></button>
          <div className="sb-sp" />
          <button type="button" className="sb-btn" title="Settings"><i className="ti ti-settings" /><span className="tt">Settings</span></button>
        </nav>

        <div className="content">
          <div className="toolbar" id="toolbar">
            <span className="page-title">Alert Queue</span>
            <span className="new-badge" style={{ display: 'none' }}>● NEW</span>
            <div className="tb-sep" />
            <div className="filter-chips">
              {(['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((level) => (
                <button
                  key={level}
                  type="button"
                  className={`chip ${level === 'CRITICAL' ? 'c-crit' : level === 'HIGH' ? 'c-high' : level === 'MEDIUM' ? 'c-med' : level === 'LOW' ? 'c-low' : ''} ${sevFilter === level ? 'active' : ''}`}
                  onClick={() => setSevFilter(level === 'ALL' ? 'ALL' : level)}
                >
                  {level === 'ALL' ? 'All' : level.charAt(0) + level.slice(1).toLowerCase()}
                  <span className="chip-n">{counts[level]}</span>
                </button>
              ))}
            </div>
            <div className="tb-sep" />
            <select value={stateFilter} onChange={(event) => setStateFilter(event.target.value)} className="state-select">
              <option value="">All States</option>
              <option value="NEW">New</option>
              <option value="ACKNOWLEDGED">Acknowledged</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="ESCALATED">Escalated</option>
              <option value="CLOSED">Closed</option>
            </select>
            <div className="tb-sp" />
            <div className="search-box">
              <i className="ti ti-search" />
              <input value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="Search alerts, entities, IDs..." />
            </div>
            <button type="button" className="tb-btn"><i className="ti ti-columns" /> Columns</button>
            <button type="button" className="tb-btn"><i className="ti ti-download" /> Export</button>
          </div>

          <div className={`batch-bar ${selectedCount > 0 ? 'show' : ''}`} id="batch-bar">
            <span className="bc-label"><span id="sel-count">{selectedCount}</span> alerts selected</span>
            <div className="bc-actions">
              <button type="button" className="ba"><i className="ti ti-user-plus" /> Assign</button>
              <button type="button" className="ba"><i className="ti ti-check" /> Acknowledge</button>
              <button type="button" className="ba"><i className="ti ti-x" /> Close</button>
              <button type="button" className="ba"><i className="ti ti-folder-plus" /> Create Case</button>
              <button type="button" className="ba danger"><i className="ti ti-thumb-down" /> False Positive</button>
            </div>
            <button type="button" className="ba" onClick={() => setSelectedRows(new Set())}><i className="ti ti-x" /></button>
          </div>

          <div className="table-area" id="table-area">
            <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
              <div className="table-wrap" id="table-wrap">
                <table id="alert-table">
                  <thead>
                    <tr>
                      <th className="col-chk"><input type="checkbox" checked={selectAllChecked} onChange={(event) => handleToggleAll(event.target.checked)} /></th>
                      <th className="col-sev"><div className="th-i">SEV</div></th>
                      <th className="col-id"><div className="th-i">ALERT ID</div></th>
                      <th className="col-title"><div className="th-i">TITLE</div></th>
                      <th className="col-src"><div className="th-i">SOURCE</div></th>
                      <th className="col-entity"><div className="th-i">ENTITY</div></th>
                      <th className="col-tactic"><div className="th-i">TACTIC</div></th>
                      <th className="col-time"><div className="th-i">DETECTED</div></th>
                      <th className="col-state"><div className="th-i">STATE</div></th>
                      <th className="col-analyst"><div className="th-i">ANALYST</div></th>
                      <th className="col-act" />
                    </tr>
                  </thead>
                  <tbody>
                    {filteredAlerts.map((alert) => {
                      const rowSelected = selectedId === alert.id;
                      return (
                        <tr key={alert.id} className={rowSelected ? 'sel' : ''} onClick={() => setSelectedId(rowSelected ? null : alert.id)}>
                          <td className="col-chk" onClick={(event) => event.stopPropagation()}>
                            <input type="checkbox" checked={selectedRows.has(alert.id)} onChange={(event) => handleToggleRow(alert.id, event.target.checked)} />
                          </td>
                          <td className="col-sev sev-cell"><div className="sev-inner"><span className={`sev-pill ${alert.severity}`}>{alert.severity}</span></div></td>
                          <td className="col-id"><span className="mono">{alert.id}</span></td>
                          <td className="col-title"><div className="title-wrap"><span className="title-txt">{alert.title}</span>{alert.correlations > 0 ? <span className="corr-tag">+{alert.correlations}</span> : null}</div></td>
                          <td className="col-src"><span className="src-pill">{alert.source}</span></td>
                          <td className="col-entity"><span className="mono">{alert.entity}</span></td>
                          <td className="col-tactic"><span className="tactic-pill">{alert.tactic}</span></td>
                          <td className="col-time"><span className="mono">{alert.detected}</span></td>
                          <td className="col-state"><span className={`state-pill st-${alert.state}`}>{formatStateLabel(alert.state)}</span></td>
                          <td className="col-analyst">{alert.analyst ? <div className="analyst-wrap"><div className="analyst-av" style={{ background: analystData[alert.analyst]?.color || '#555' }}>{analystData[alert.analyst]?.initials || '?'}</div><span className="analyst-name">{formatAnalyst(alert.analyst)}</span></div> : <span className="unassigned">Unassigned</span>}</td>
                          <td className="col-act"><div className="act-wrap"><button type="button" className="act-ic has-tip" data-tip="Acknowledge"><i className="ti ti-check" /></button><button type="button" className="act-ic has-tip" data-tip="More"><i className="ti ti-dots" /></button></div></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="statusbar">
                <div className="sb-item ok"><i className="ti ti-circle-check" /> Pipeline connected</div>
                <div className="sb-item"><i className="ti ti-database" /> <span className="sb-showing">{filteredAlerts.length} of {ALERTS.length}</span> alerts</div>
                <div className="sb-item r"><i className="ti ti-alert-triangle" /> <span className="sb-crit">{criticalOpen}</span> critical unacknowledged</div>
                <div className="sb-sp2" />
                <div className="sb-pager"><button type="button" className="pg-b"><i className="ti ti-chevron-left" /></button><span className="pg-label">Page 1 / 1</span><button type="button" className="pg-b"><i className="ti ti-chevron-right" /></button></div>
              </div>
            </div>

            <div className="dp" id="detail-panel">
              {!selectedAlert ? (
                <div className="dp-empty">
                  <i className="ti ti-list-search" />
                  <div className="dp-empty-t">No alert selected</div>
                  <div className="dp-empty-s">Click any row to inspect the alert, view enrichment data, and take action.</div>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
                  <div className="dp-hdr">
                    <div className="dp-top">
                      <div className="dp-title">{selectedAlert.title}</div>
                      <button type="button" className="dp-close" onClick={() => setSelectedId(null)}><i className="ti ti-x" /></button>
                    </div>
                    <div className="dp-meta">
                      <span className={`sev-pill ${selectedAlert.severity}`} style={{ fontSize: '9px' }}>{selectedAlert.severity}</span>
                      <span className="dp-id">{selectedAlert.id}</span>
                      <span className={`state-pill st-${selectedAlert.state}`} style={{ fontSize: '9px' }}>{formatStateLabel(selectedAlert.state)}</span>
                    </div>
                  </div>
                  <div className="dp-acts">
                    <button type="button" className="dp-act primary"><i className="ti ti-user-plus" /> Assign</button>
                    <button type="button" className="dp-act"><i className="ti ti-check" /> Ack</button>
                    <button type="button" className="dp-act"><i className="ti ti-folder-plus" /> Case</button>
                    <button type="button" className="dp-act"><i className="ti ti-bolt" /> Respond</button>
                  </div>
                  <div className="dp-body">
                    <div className="dp-sec">
                      <div className="dp-sec-lbl">Overview</div>
                      <div className="kv-grid" style={{ marginBottom: '8px' }}>
                        <div className="kv"><div className="k">Source</div><div className="v">{selectedAlert.source}</div></div>
                        <div className="kv"><div className="k">Entity</div><div className="v">{selectedAlert.entity}</div></div>
                        <div className="kv"><div className="k">Detected</div><div className="v">{selectedAlert.detected}</div></div>
                        <div className="kv"><div className="k">Analyst</div><div className="v dim">{selectedAlert.analyst ?? 'Unassigned'}</div></div>
                      </div>
                      <div style={{ marginBottom: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '9px', color: 'var(--t-3)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Risk Score</span>
                        <span style={{ fontFamily: 'var(--ff-data)', fontSize: '9px', color: selectedAlert.risk >= 80 ? 'var(--crit)' : selectedAlert.risk >= 60 ? 'var(--high)' : selectedAlert.risk >= 40 ? 'var(--med)' : 'var(--state-cls)' }}>{selectedAlert.risk >= 80 ? 'CRITICAL' : selectedAlert.risk >= 60 ? 'HIGH' : selectedAlert.risk >= 40 ? 'MEDIUM' : 'LOW'}</span>
                      </div>
                      <div className="risk-row">
                        <div className="risk-track"><div className="risk-fill" style={{ width: `${selectedAlert.risk}%`, background: selectedAlert.risk >= 80 ? 'var(--crit)' : selectedAlert.risk >= 60 ? 'var(--high)' : selectedAlert.risk >= 40 ? 'var(--med)' : 'var(--state-cls)' }} /></div>
                        <div className="risk-label" style={{ color: selectedAlert.risk >= 80 ? 'var(--crit)' : selectedAlert.risk >= 60 ? 'var(--high)' : selectedAlert.risk >= 40 ? 'var(--med)' : 'var(--state-cls)' }}>{selectedAlert.risk}</div>
                      </div>
                      <div style={{ marginTop: '10px', fontSize: '11px', color: 'var(--t-2)', lineHeight: 1.5 }}>{selectedAlert.desc}</div>
                    </div>
                    <div className="dp-sec">
                      <div className="dp-sec-lbl">MITRE ATT&CK</div>
                      <div className="mitre-card">
                        <div className="mitre-half"><div className="mitre-lbl">Tactic</div><div className="mitre-val">{selectedAlert.tactic}</div></div>
                        <div className="mitre-half"><div className="mitre-lbl">Technique</div><div className="mitre-val" style={{ fontSize: '10px' }}>{selectedAlert.technique}</div></div>
                      </div>
                    </div>
                    <div className="dp-sec">
                      <div className="dp-sec-lbl">Indicators of Compromise</div>
                      <table className="ioc-tbl">{selectedAlert.iocs.map((ioc) => (
                        <tr key={`${ioc.type}-${ioc.val}`}>
                          <td className="ioc-type">{ioc.type}</td>
                          <td className="ioc-val">{ioc.val}</td>
                          <td className="ioc-conf"><span className={ioc.conf >= 85 ? 'conf-h' : ioc.conf >= 60 ? 'conf-m' : 'conf-l'}>{ioc.conf}%</span></td>
                        </tr>
                      ))}</table>
                    </div>
                    <div className="dp-sec">
                      <div className="dp-sec-lbl">Enrichment</div>
                      {selectedAlert.enrichment.abuseipdb || selectedAlert.enrichment.virustotal || selectedAlert.enrichment.greynoise ? (
                        <div className="kv-grid">
                          {selectedAlert.enrichment.abuseipdb ? <div className="kv"><div className="k">AbuseIPDB</div><div className="v dim">{selectedAlert.enrichment.abuseipdb}</div></div> : null}
                          {selectedAlert.enrichment.virustotal ? <div className="kv"><div className="k">VirusTotal</div><div className="v dim">{selectedAlert.enrichment.virustotal}</div></div> : null}
                          {selectedAlert.enrichment.greynoise ? <div className="kv"><div className="k">GreyNoise</div><div className="v dim">{selectedAlert.enrichment.greynoise}</div></div> : null}
                        </div>
                      ) : (
                        <div style={{ fontSize: '10px', color: 'var(--t-4)' }}>No enrichment data available.</div>
                      )}
                    </div>
                    <div className="dp-sec">
                      <div className="dp-sec-lbl">Timeline</div>
                      <div className="tl-list">{selectedAlert.timeline.map((step) => (
                        <div key={`${step.t}-${step.txt}`} className="tl-row">
                          <div className="tl-time">{step.t}</div>
                          <div className={`tl-dot ${step.act ? 'active' : ''}`} />
                          <div className="tl-text">{step.txt}</div>
                        </div>
                      ))}</div>
                    </div>
                    <div className="dp-sec">
                      <div className="dp-sec-lbl">Analyst Notes</div>
                      <textarea className="notes-ta" placeholder="Add investigation notes, hypothesis, findings..." />
                      <div className="notes-save"><button type="button" className="notes-save-btn"><i className="ti ti-device-floppy" style={{ fontSize: '11px' }} /> Save Note</button></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
