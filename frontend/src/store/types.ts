/** Centralized type definitions for the global state */

export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
export type AlertState = 'NEW' | 'ACKNOWLEDGED' | 'IN_PROGRESS' | 'ESCALATED' | 'CLOSED' | 'FALSE_POSITIVE';

export interface Ioc {
    type: string;
    val: string;
    conf: number;
}

export interface TimelineStep {
    t: string;
    txt: string;
    act?: boolean;
}

export interface Enrichment {
    abuseipdb: string | null;
    virustotal: string | null;
    greynoise: string | null;
}

export interface Alert {
    id: string;
    severity: Severity;
    title: string;
    source: string;
    entity: string;
    tactic: string;
    technique: string;
    detected: string;
    state: AlertState;
    analyst: string | null;
    correlations: number;
    risk: number;
    desc: string;
    iocs: Ioc[];
    timeline: TimelineStep[];
    enrichment: Enrichment;
}
