import { useEffect, useMemo, useState } from 'react';
import '../styles/alerts-futuristic.css';
import { useAlertUIStore } from '../store/useAlertUIStore';
import type { Severity, Ioc, TimelineStep } from '../store/types';
import { MOCK_ALERTS } from '../data/mockAlerts';
import { SEV_ORDER, ANALYSTS, formatStateLabel } from '../utils/alertUtils';

const ALERTS = MOCK_ALERTS;

type SortKey = 'severity' | 'id' | 'entity' | 'detected';
export default function AlertsPage() {
  const sevFilter = useAlertUIStore((s) => s.sevFilter);
const setSevFilter = useAlertUIStore((s) => s.setSevFilter);

const selectedId = useAlertUIStore(
  (s) => s.selectedAlertId
);
const setSelectedId = useAlertUIStore(
  (s) => s.setSelectedAlertId
);

const selectedRows = useAlertUIStore(
  (s) => s.selectedRows
);
const setSelectedRows = useAlertUIStore(
  (s) => s.setSelectedRows
);

const searchQuery = useAlertUIStore(
  (s) => s.searchQuery
);
const setSearchQuery = useAlertUIStore(
  (s) => s.setSearchQuery
);

const stateFilter = useAlertUIStore(
  (s) => s.stateFilter
);
const setStateFilter = useAlertUIStore(
  (s) => s.setStateFilter
);

const sortKey = useAlertUIStore(
  (s) => s.sortKey
);
const setSortKey = useAlertUIStore(
  (s) => s.setSortKey
);

const sortDir = useAlertUIStore(
  (s) => s.sortDir
);
const setSortDir = useAlertUIStore(
  (s) => s.setSortDir
);
  const [rate, setRate] = useState<number>(Math.floor(Math.random() * 200 + 400));

  useEffect(() => {
    const interval = window.setInterval(() => setRate(Math.floor(Math.random() * 200 + 400)), 3000);
    return () => window.clearInterval(interval);
  }, []);

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
      if (sortKey === 'severity') return (SEV_ORDER[a.severity] - SEV_ORDER[b.severity]) * sortDir;
      if (sortKey === 'id') return a.id.localeCompare(b.id) * sortDir;
      if (sortKey === 'entity') return a.entity.localeCompare(b.entity) * sortDir;
      return sortDir === 1 ? a.detected.localeCompare(b.detected) : b.detected.localeCompare(a.detected);
    });
  }, [sevFilter, stateFilter, searchQuery, sortKey, sortDir]);

  const counts = useMemo(() => {
    const c: Record<'ALL' | Severity, number> = { ALL: ALERTS.length, CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, INFO: 0 };
    ALERTS.forEach((alert) => {
      c[alert.severity] += 1;
    });
    return c;
  }, []);

  const selectedAlert = useMemo(() => ALERTS.find((alert) => alert.id === selectedId) ?? null, [selectedId]);
  const criticalOpen = ALERTS.filter((alert) => alert.severity === 'CRITICAL' && alert.state !== 'CLOSED' && alert.state !== 'FALSE_POSITIVE').length;
  const openAlerts = ALERTS.filter((alert) => alert.state !== 'CLOSED' && alert.state !== 'FALSE_POSITIVE').length;

  const toggleRow = (id: string, checked: boolean) => {
    const next = new Set(selectedRows);
    if (checked) next.add(id);
    else next.delete(id);
    setSelectedRows(next);
  };

  const toggleAll = (checked: boolean) => {
    setSelectedRows(checked ? new Set(filteredAlerts.map((alert) => alert.id)) : new Set());
  };

  const clearSelection = () => setSelectedRows(new Set());
  const selectRow = (id: string) => setSelectedId((current) => (current === id ? null : id));
  const batchAction = (_action: string) => setSelectedRows(new Set());

  const renderIocs = (iocs: Ioc[]) =>
    iocs.map((ioc) => (
      <tr key={`${ioc.type}-${ioc.val}`}>
        <td className="ioc-type">{ioc.type}</td>
        <td className="ioc-val">{ioc.val}</td>
        <td className="ioc-conf">
          <span className={ioc.conf >= 85 ? 'conf-h' : ioc.conf >= 60 ? 'conf-m' : 'conf-l'}>{ioc.conf}%</span>
        </td>
      </tr>
    ));

  const renderTimeline = (timeline: TimelineStep[]) =>
    timeline.map((step) => (
      <div key={`${step.t}-${step.txt}`} className="tl-row">
        <div className="tl-time">{step.t}</div>
        <div className={`tl-dot ${step.act ? 'active' : ''}`} />
        <div className="tl-text">{step.txt}</div>
      </div>
    ));

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
                  onClick={() => setSevFilter(level)}
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
              <button type="button" className="ba" onClick={() => batchAction('assign')}><i className="ti ti-user-plus" /> Assign</button>
              <button type="button" className="ba" onClick={() => batchAction('ack')}><i className="ti ti-check" /> Acknowledge</button>
              <button type="button" className="ba" onClick={() => batchAction('close')}><i className="ti ti-x" /> Close</button>
              <button type="button" className="ba" onClick={() => batchAction('case')}><i className="ti ti-folder-plus" /> Create Case</button>
              <button type="button" className="ba danger" onClick={() => batchAction('fp')}><i className="ti ti-thumb-down" /> False Positive</button>
            </div>
            <button type="button" className="ba" onClick={clearSelection}><i className="ti ti-x" /></button>
          </div>

          <div className="table-area" id="table-area">
            <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
              <div className="table-wrap" id="table-wrap">
                <table id="alert-table">
                  <thead>
                    <tr>
                      <th className="col-chk"><input type="checkbox" checked={selectAllChecked} onChange={(event) => toggleAll(event.target.checked)} /></th>
                      <th className={`col-sev ${sortKey === 'severity' ? 'sorted' : ''}`} onClick={() => { setSortKey('severity'); setSortDir(sortDir === 1 ? -1 : 1); }}><div className="th-i">SEV<i className="ti ti-selector sort-ic" /></div></th>
                      <th className={`col-id ${sortKey === 'id' ? 'sorted' : ''}`} onClick={() => { setSortKey('id'); setSortDir(sortDir === 1 ? -1 : 1); }}><div className="th-i">ALERT ID<i className="ti ti-selector sort-ic" /></div></th>
                      <th className="col-title"><div className="th-i">TITLE</div></th>
                      <th className="col-src"><div className="th-i">SOURCE</div></th>
                      <th className={`col-entity ${sortKey === 'entity' ? 'sorted' : ''}`} onClick={() => { setSortKey('entity'); setSortDir(sortDir === 1 ? -1 : 1); }}><div className="th-i">ENTITY<i className="ti ti-selector sort-ic" /></div></th>
                      <th className="col-tactic"><div className="th-i">TACTIC</div></th>
                      <th className={`col-time ${sortKey === 'detected' ? 'sorted' : ''}`} onClick={() => { setSortKey('detected'); setSortDir(sortDir === 1 ? -1 : 1); }}><div className="th-i">DETECTED<i className="ti ti-selector sort-ic" /></div></th>
                      <th className="col-state"><div className="th-i">STATE</div></th>
                      <th className="col-analyst"><div className="th-i">ANALYST</div></th>
                      <th className="col-act" />
                    </tr>
                  </thead>
                  <tbody>
                    {filteredAlerts.map((alert) => {
                      const rowSelected = selectedId === alert.id;
                      return (
                        <tr key={alert.id} data-s={alert.severity} className={rowSelected ? 'sel' : ''} onClick={() => selectRow(alert.id)}>
                          <td className="col-chk" onClick={(event) => event.stopPropagation()}>
                            <input type="checkbox" checked={selectedRows.has(alert.id)} onChange={(event) => toggleRow(alert.id, event.target.checked)} />
                          </td>
                          <td className="col-sev sev-cell"><div className="sev-inner"><span className={`sev-pill ${alert.severity}`}>{alert.severity}</span></div></td>
                          <td className="col-id"><span className="mono">{alert.id}</span></td>
                          <td className="col-title"><div className="title-wrap"><span className="title-txt">{alert.title}</span>{alert.correlations > 0 ? <span className="corr-tag">+{alert.correlations}</span> : null}</div></td>
                          <td className="col-src"><span className="src-pill">{alert.source}</span></td>
                          <td className="col-entity"><span className="mono">{alert.entity}</span></td>
                          <td className="col-tactic"><span className="tactic-pill">{alert.tactic}</span></td>
                          <td className="col-time"><span className="mono">{alert.detected}</span></td>
                          <td className="col-state"><span className={`state-pill st-${alert.state}`}>{formatStateLabel(alert.state)}</span></td>
                          <td className="col-analyst">{alert.analyst ? <div className="analyst-wrap"><div className="analyst-av" style={{ background: ANALYSTS[alert.analyst]?.color || '#555' }}>{ANALYSTS[alert.analyst]?.initials || '?'}</div><span className="analyst-name">{alert.analyst.split(' ')[1]}</span></div> : <span className="unassigned">Unassigned</span>}</td>
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
                      <table className="ioc-tbl">{renderIocs(selectedAlert.iocs)}</table>
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
                      <div className="tl-list">{renderTimeline(selectedAlert.timeline)}</div>
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


