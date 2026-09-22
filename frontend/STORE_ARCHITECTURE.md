# Centralized State Management - Architecture Migration

## Completed: Zustand Store Setup

### Stores Created

#### 1. `src/store/types.ts`
- Centralized type definitions for: `Alert`, `Severity`, `AlertState`, `Ioc`, `TimelineStep`, `Enrichment`
- Single source of truth for all alert-related types across the application

#### 2. `src/store/useAlertUIStore.ts`
**Consolidates all UI state** that was previously scattered across component `useState`:
- `selectedAlertId` — which alert row is expanded
- `selectedRows` — Set of checkbox-selected alerts
- `sevFilter` — severity filter (ALL, CRITICAL, HIGH, MEDIUM, LOW)
- `stateFilter` — alert state filter
- `searchQuery` — search input value
- `sortKey` & `sortDir` — column sort state

**Actions exposed:**
- `setSelectedAlertId()`, `toggleSelectedRow()`, `setSearchQuery()`, etc.
- `resetFilters()` — atomic reset of all UI state

#### 3. `src/store/useSystemStore.ts`
**Holds system-level metrics** (previously local useState):
- `eventRate` — events per second
- `pipelineHealth` — system health percentage
- `openAlertsCount`, `criticalAlertsCount`
- `isHealthy`, `isReady` — system readiness flags

**Actions:**
- Individual setters: `setEventRate()`, `setPipelineHealth()`, etc.
- Batch update: `updateMetrics()` for multiple changes at once

### Migration Example: NeptuneConsole

**Before (Fragmented State):**
```tsx
const [selectedId, setSelectedId] = useState<string | null>(null);
const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set());
const [sevFilter, setSevFilter] = useState<'ALL' | Severity>('ALL');
const [rate, setRate] = useState<number>(...);
// 7 separate useState calls
```

**After (Centralized State):**
```tsx
// Read from stores via granular selectors
const selectedId = useAlertUIStore((state) => state.selectedAlertId);
const sevFilter = useAlertUIStore((state) => state.sevFilter);
const rate = useSystemStore((state) => state.eventRate);

// Dispatch actions directly
const setSevFilter = useAlertUIStore((state) => state.setSevFilter);
const setEventRate = useSystemStore((state) => state.setEventRate);

// Uses are identical:
setSevFilter('CRITICAL');
setEventRate(520);
```

## Why This Architecture Works

### Single Source of Truth
- All 7 pages (`NeptuneConsole`, `Alerts`, `OperationalDashboard`, etc.) now read from the same store
- Navigating between pages doesn't destroy state
- No re-fetching needed when returning to a page

### Granular Subscriptions
- `useAlertUIStore((state) => state.severity)` only triggers re-render if severity changes
- Prevents unnecessary renders of the entire component tree
- Fixes the "Jank" problem at scale (50+ alerts, high-frequency updates)

### Logic Decoupling
- **Business logic** lives in the Store (what data to keep, how to filter)
- **Presentation** lives in Components (how to render)
- Can redesign entire UI without touching store logic

## Pattern for Migrating Other Components

### Step 1: Identify All useState + useCallback
```tsx
// Find these patterns and note what they control:
const [alerts, setAlerts] = useState([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);
```

### Step 2: Create Store for That Domain
```tsx
// src/store/useAlertsStore.ts (or useLoadingStore, etc.)
export const useXyzStore = create((set) => ({
  // State
  alerts: [],
  loading: false,
  error: null,
  
  // Actions
  setAlerts: (alerts) => set({ alerts }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));
```

### Step 3: Replace useState with Store Selectors
```tsx
// OLD:
const [alerts, setAlerts] = useState([]);

// NEW:
const alerts = useAlertsStore((state) => state.alerts);
const setAlerts = useAlertsStore((state) => state.setAlerts);
```

### Step 4: Import and Use
```tsx
import { useAlertsStore } from '../store/useAlertsStore';

function MyComponent() {
  const alerts = useAlertsStore((state) => state.alerts);
  // ... rest of component
}
```

## Next Components to Migrate

1. **Alerts.tsx** — Currently has 7 useState calls; uses identical filter structure to NeptuneConsole
2. **OperationalDashboard.tsx** — Has `[alerts, setAlerts]`, `[feed, setFeed]`, `[searchTerm, setSearchTerm]`
3. **Dashboard.tsx** — System health/info state can move to `useSystemStore`
4. **Login.tsx** — Can use AuthContext + new `useAuthStore` for session persistence

## Store File Locations
```
frontend/src/store/
├── types.ts                 # Shared type definitions
├── useAlertStore.ts         # Alert data (already existed)
├── useAlertUIStore.ts       # NEW: UI filters & selection
├── useSystemStore.ts        # NEW: System metrics & health
└── (future: useAuthStore.ts, useSearchStore.ts, etc.)
```

## Key Principle

**"Data that flows together lives together."**

- Alert metadata (severity, state, entity) → `useAlertStore` or API
- UI selections (which row is selected, what's the filter) → `useAlertUIStore`
- System state (health, readiness) → `useSystemStore`
- Authentication (token, user profile) → (existing `AuthContext` + potential `useAuthStore`)

Once all UI state is centralized, you can easily build:
- Undo/redo (snapshot and restore previous store state)
- Time-travel debugging (inspect store history)
- Persistence (save/load store to localStorage)
- Real-time sync (WebSocket updates push directly to store)
