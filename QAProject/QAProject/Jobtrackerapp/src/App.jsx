import { useEffect, useMemo, useRef, useState } from 'react';
import {
  DndContext,
  PointerSensor,
  closestCenter,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import RecommendedJobs from './RecommendedJobs';

const COLUMN_ORDER = [
  'job-saved',
  'applied',
  'in-progress',
  'follow-up',
  'interview',
  'offer',
  'rejected',
];

const STATUS_LABELS = {
  'job-saved': 'Job Saved',
  applied: 'Applied',
  'in-progress': 'In Progress',
  'follow-up': 'Follow-up',
  interview: 'Interview',
  offer: 'Offer',
  rejected: 'Rejected',
};

const THEME_OPTIONS = ['light', 'dark', 'pastel', 'contrast'];

const INITIAL_COLUMNS = {
  'job-saved': [],
  applied: [],
  'in-progress': [],
  'follow-up': [],
  interview: [],
  offer: [],
  rejected: [],
};

const BOARD_KEY = 'jobPathwayBoard';
const THEME_KEY = 'jobPathwayTheme';

const formatDate = (iso) => {
  const date = new Date(iso);
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
};

function useColumnData() {
  const [columns, setColumns] = useState(() => {
    try {
      const stored = localStorage.getItem(BOARD_KEY);
      if (stored) return JSON.parse(stored);
    } catch (error) {
      console.error('Failed to load saved board', error);
    }
    return INITIAL_COLUMNS;
  });

  useEffect(() => {
    localStorage.setItem(BOARD_KEY, JSON.stringify(columns));
  }, [columns]);

  return [columns, setColumns];
}

function usePersistedTheme() {
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem(THEME_KEY) || 'light';
    } catch {
      return 'light';
    }
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  return [theme, setTheme];
}

function DraggableCard({ card, onSelect, onEdit, onDelete, searchQuery, onUploadResume, onRemoveResume }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: card.id,
  });

  const style = {
    transform: CSS.Translate.toString(transform),
  };

  return (
    <article
      ref={setNodeRef}
      data-card-id={card.id}
      className={`card ${isDragging ? 'dragging' : ''} ${(searchQuery || '').trim() && (((card.company||'') + ' ' + (card.role||'')).toLowerCase().includes((searchQuery||'').toLowerCase()) ) ? 'highlight' : ''}`}
      style={style}
      {...attributes}
      {...listeners}
      onClick={() => onSelect(card)}
    >
      <div className="card-header">
        <div>
          <h3>{card.company || 'Untitled Company'}</h3>
          <p>{card.role || 'Open role'}</p>
        </div>
        <span className="badge">{STATUS_LABELS[card.stage]}</span>
      </div>

      <div className="card-body">
        <p>{card.notes || 'No description yet.'}</p>
      </div>

      <div className="card-footer">
        <div>
          <p>{card.email || card.phone || 'No contact details'}</p>
          {card.phone && <p className="muted">Phone: {card.phone}</p>}
          {card.resume && card.resume.name ? (
            <p className="muted resume-row">
              📄 <a href={card.resume.dataUrl} target="_blank" rel="noreferrer" download={card.resume.name} className="resume-link">{card.resume.name}</a>
              <button type="button" className="tiny" onClick={(e) => { e.stopPropagation(); onRemoveResume(card.id); }}>Remove</button>
            </p>
          ) : (
            <label className="upload-inline">
              <input
                type="file"
                accept=".pdf,.doc,.docx"
                style={{ display: 'none' }}
                onChange={(e) => { e.stopPropagation(); const f = e.target.files?.[0]; if (f) onUploadResume(card.id, f); }}
              />
              <button type="button" className="tiny" onClick={(e) => e.stopPropagation()}>Upload Resume</button>
            </label>
          )}
        </div>
        <div className="card-actions">
          <button type="button" onClick={(event) => { event.stopPropagation(); onEdit(card); }}>
            Edit
          </button>
          <button type="button" className="danger" onClick={(event) => { event.stopPropagation(); onDelete(card.id); }}>
            Delete
          </button>
        </div>
      </div>
    </article>
  );
}

function DropColumn({ id, title, count, children, onAdd }) {
  const { setNodeRef, isOver } = useDroppable({ id });
  return (
    <section ref={setNodeRef} className={`column ${id} ${isOver ? 'over' : ''}`}>
      <header>
        <div>
          <h2>{title}</h2>
          <span className="count">{count}</span>
        </div>
        <button className="small" type="button" onClick={() => onAdd(id)}>
          + Add
        </button>
      </header>
      <div className="cards-container">
        {children}
      </div>
    </section>
  );
}

function App() {
  const [columns, setColumns] = useColumnData();
  const [theme, setTheme] = usePersistedTheme();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOrder, setSortOrder] = useState('newest');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingCard, setEditingCard] = useState(null);
  const [formState, setFormState] = useState({
    id: '',
    company: '',
    role: '',
    email: '',
    phone: '',
    resume: '',
    notes: '',
    stage: 'job-saved',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  });
  const [isAutoScrollPaused, setIsAutoScrollPaused] = useState(false);
  const stageScrollRef = useRef(null);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  const allCards = useMemo(() => Object.values(columns).flat(), [columns]);
  const statusTotals = useMemo(
    () => COLUMN_ORDER.reduce((acc, stage) => {
      acc[stage] = columns[stage].length;
      return acc;
    }, {}),
    [columns]
  );
  const totalCards = allCards.length;
  const firstAdded = useMemo(() => {
    if (!allCards.length) return '-';
    const oldest = allCards.reduce((min, card) => (new Date(card.createdAt) < new Date(min.createdAt) ? card : min), allCards[0]);
    return formatDate(oldest.createdAt);
  }, [allCards]);
  const appliedToInterview = statusTotals.applied ? Math.round((statusTotals.interview / statusTotals.applied) * 100) : 0;
  const statusDistribution = useMemo(
    () => COLUMN_ORDER.map((stage) => ({
      stage,
      count: statusTotals[stage],
      percent: totalCards ? Math.round((statusTotals[stage] / totalCards) * 100) : 0,
    })),
    [statusTotals, totalCards]
  );

  const [rangeSelectorOpen, setRangeSelectorOpen] = useState(false);
  const [rangeStart, setRangeStart] = useState(1); // default Applied index
  const [rangeEnd, setRangeEnd] = useState(4); // default Interview index
  const [recPage, setRecPage] = useState(0);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const scrollStages = (direction) => {
    const container = stageScrollRef.current;
    if (!container) return;
    const step = container.clientWidth * 0.6;
    const next = direction === 'left' ? Math.max(container.scrollLeft - step, 0) : Math.min(container.scrollLeft + step, container.scrollWidth - container.clientWidth);
    container.scrollTo({ left: next, behavior: 'smooth' });
    setIsAutoScrollPaused(true);
    window.clearTimeout(container._resumeTimeout);
    container._resumeTimeout = window.setTimeout(() => setIsAutoScrollPaused(false), 3200);
  };

  useEffect(() => {
    const interval = window.setInterval(() => {
      if (isAutoScrollPaused || !stageScrollRef.current) return;
      const container = stageScrollRef.current;
      const maxScroll = container.scrollWidth - container.clientWidth;
      if (maxScroll <= 0) return;
      const next = container.scrollLeft + container.clientWidth * 0.7;
      if (next >= maxScroll - 10) {
        container.scrollTo({ left: 0, behavior: 'smooth' });
      } else {
        container.scrollTo({ left: next, behavior: 'smooth' });
      }
    }, 4200);

    return () => window.clearInterval(interval);
  }, [isAutoScrollPaused]);

  const filteredCards = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    const matched = allCards.filter((card) => {
      if (!query) return true;
      return [card.company, card.role].some((value) => value.toLowerCase().includes(query));
    });

    return matched.sort((a, b) => {
      const dateA = new Date(a.updatedAt).getTime();
      const dateB = new Date(b.updatedAt).getTime();
      return sortOrder === 'newest' ? dateB - dateA : dateA - dateB;
    });
  }, [allCards, searchQuery, sortOrder]);

  const filteredCounts = useMemo(
    () => COLUMN_ORDER.reduce((acc, stage) => {
      acc[stage] = filteredCards.filter((card) => card.stage === stage).length;
      return acc;
    }, {}),
    [filteredCards]
  );

  const visibleStatusDistribution = useMemo(() => {
    if (!rangeSelectorOpen) return statusDistribution;
    return statusDistribution.filter((s, idx) => idx >= rangeStart && idx <= rangeEnd);
  }, [statusDistribution, rangeSelectorOpen, rangeStart, rangeEnd]);

  const performSearch = () => {
    if (!searchQuery) return;
    const q = searchQuery.trim().toLowerCase();
    const found = allCards.find((card) => ((card.company || '') + ' ' + (card.role || '')).toLowerCase().includes(q));
    if (!found) return alert('No matching card found');
    const el = document.querySelector(`[data-card-id="${found.id}"]`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.classList.add('flash');
      setTimeout(() => el.classList.remove('flash'), 1800);
    }
  };

  const followUpAlerts = useMemo(() => {
    const list = (columns['follow-up'] || []).map((card) => {
      const days = Math.floor((Date.now() - new Date(card.updatedAt).getTime()) / (1000 * 60 * 60 * 24));
      return { ...card, days };
    }).filter((c) => c.days > 4);
    return list;
  }, [columns]);

  const handleUploadResume = (cardId, file) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target.result;
      setColumns((prev) => {
        const next = { ...prev };
        for (const stage of COLUMN_ORDER) {
          next[stage] = next[stage].map((c) => c.id === cardId ? { ...c, resume: { name: file.name, dataUrl } } : c);
        }
        return next;
      });
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveResume = (cardId) => {
    setColumns((prev) => {
      const next = { ...prev };
      for (const stage of COLUMN_ORDER) {
        next[stage] = next[stage].map((c) => c.id === cardId ? { ...c, resume: null } : c);
      }
      return next;
    });
  };


  const handleDragEnd = ({ active, over }) => {
    if (!over || active.id === over.id) return;
    const cardId = active.id;
    const sourceStage = Object.entries(columns).find(([, cards]) => cards.some((card) => card.id === cardId));
    if (!sourceStage) return;
    const [fromStage] = sourceStage;
    const toStage = over.id;
    if (fromStage === toStage) return;

    const card = sourceStage[1].find((item) => item.id === cardId);
    const updatedCard = { ...card, stage: toStage, updatedAt: new Date().toISOString() };
    setColumns((prev) => ({
      ...prev,
      [fromStage]: prev[fromStage].filter((item) => item.id !== cardId),
      [toStage]: [updatedCard, ...prev[toStage]],
    }));
  };

  const openForm = (stage) => {
    setEditingCard(null);
    setFormState({
      id: `card-${Date.now()}`,
      company: '',
      role: '',
      email: '',
      phone: '',
      resume: '',
      notes: '',
      stage,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    });
    setModalOpen(true);
  };

  const openEdit = (card) => {
    setEditingCard(card);
    setFormState({ ...card });
    setModalOpen(true);
  };

  const handleSave = (event) => {
    event.preventDefault();
    if (!formState.role.trim() || !formState.stage.trim()) {
      alert('Please enter the required fields: Job title and card selection.');
      return;
    }
    const normalized = {
      ...formState,
      company: formState.company.trim(),
      role: formState.role.trim(),
      email: formState.email.trim(),
      phone: formState.phone.trim(),
      resume: formState.resume,
      notes: formState.notes.trim(),
      updatedAt: new Date().toISOString(),
    };

    setColumns((prev) => {
      const next = { ...prev };
      if (editingCard) {
        next[editingCard.stage] = next[editingCard.stage].map((card) =>
          card.id === normalized.id ? normalized : card
        );
        if (editingCard.stage !== normalized.stage) {
          next[editingCard.stage] = next[editingCard.stage].filter((card) => card.id !== normalized.id);
          next[normalized.stage] = [normalized, ...(next[normalized.stage] || [])];
        }
      } else {
        next[normalized.stage] = [normalized, ...next[normalized.stage]];
      }
      return next;
    });

    setModalOpen(false);
  };

  const handleDelete = (cardId) => {
    setColumns((prev) => {
      const next = { ...prev };
      for (const stage of COLUMN_ORDER) {
        next[stage] = next[stage].filter((card) => card.id !== cardId);
      }
      return next;
    });
  };

  const handleImport = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const parsed = JSON.parse(text);
      const valid = COLUMN_ORDER.every((stage) => Array.isArray(parsed[stage]));
      if (!valid) throw new Error('Imported JSON does not match board format.');
      setColumns(parsed);
    } catch (error) {
      alert('Import failed: ' + error.message);
    }
  };

  const handleExport = () => {
    const blob = new Blob([JSON.stringify(columns, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'job-pathway-board.json';
    anchor.click();
    URL.revokeObjectURL(url);
  };


  return (
    <div className="app-shell">
      <div className="topbar">
        <div>
          <p className="eyebrow">Job Pathway</p>
          <h1>Job application tracker</h1>
          <p className="subtitle">Organize applications, move cards across stages, and keep follow-ups in view.</p>
        </div>

        <div className="top-actions">
          <button type="button" className="primary add-job round" onClick={() => openForm('job-saved')}>
            Add Job
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div className="notifications">
              <button type="button" className="icon-bell" onClick={() => setNotificationsOpen((s) => !s)}>
                🔔
                {followUpAlerts.length > 0 ? <span className="badge">{followUpAlerts.length}</span> : null}
              </button>
              {notificationsOpen ? (
                <div className="notifications-panel">
                  {followUpAlerts.length === 0 ? (
                    <div className="muted">You will be notified if a card stays in Follow-up for more than 4 days.</div>
                  ) : (
                    <div className="notif-list">
                      {followUpAlerts.map((c) => (
                        <div key={c.id} className="notif-row">
                          <div className="notif-title">{c.company || c.role}</div>
                          <div className="notif-days">{c.days} days</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : null}
            </div>
            <div className="theme-switcher">
              {THEME_OPTIONS.map((option) => (
                <button
                  key={option}
                  type="button"
                  className={theme === option ? 'active' : ''}
                  onClick={() => setTheme(option)}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <section className="dashboard-panel">
        <div className="dashboard-header">
          <div>
            <p className="eyebrow">Cards dashboard</p>
            <h2>Status distribution & insights</h2>
            <p className="subtitle">Review totals, conversion, and status counts across your application pipeline.</p>
          </div>
          <div className="dashboard-actions">
            <label>
              Search
              <div style={{display:'flex',gap:8}}>
                <input
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="Company or role..."
                />
                <button type="button" onClick={performSearch} className="small">Search</button>
              </div>
            </label>
          </div>
        </div>

        <div className="summary-grid">
          <div className="stat-card">
            <span>Total cards</span>
            <strong>{totalCards}</strong>
          </div>
          <div
            className="stat-card clickable"
            onClick={() => setRangeSelectorOpen((s) => !s)}
            title="Click to select a status range"
          >
            <span>Applied → Interview</span>
            <strong>{appliedToInterview}%</strong>
          </div>
          <div className="stat-card">
            <span>First added</span>
            <strong>{firstAdded}</strong>
          </div>
        </div>

        {rangeSelectorOpen && (
          <div className="range-selector">
            <label>
              Start: <strong>{STATUS_LABELS[COLUMN_ORDER[rangeStart]]}</strong>
              <input type="range" min={0} max={COLUMN_ORDER.length - 1} value={rangeStart} onChange={(e) => {
                const v = Number(e.target.value);
                if (v > rangeEnd) setRangeEnd(v);
                setRangeStart(v);
              }} />
            </label>
            <label>
              End: <strong>{STATUS_LABELS[COLUMN_ORDER[rangeEnd]]}</strong>
              <input type="range" min={0} max={COLUMN_ORDER.length - 1} value={rangeEnd} onChange={(e) => {
                const v = Number(e.target.value);
                if (v < rangeStart) setRangeStart(v);
                setRangeEnd(v);
              }} />
            </label>
            <div style={{display:'flex',gap:8,alignItems:'center'}}>
              <button type="button" onClick={() => { setRangeSelectorOpen(false); setRangeStart(1); setRangeEnd(4); }}>Reset</button>
            </div>
          </div>
        )}

        <div className="bars-grid">
          {visibleStatusDistribution.map(({ stage, count, percent }) => (
            <div key={stage} className={`status-bar-row status-${stage}`}>
              <div className="status-bar-label">
                <span className="status-chip">{STATUS_LABELS[stage]}</span>
                <div className="status-bar-label-right">
                  <strong>{count}</strong>
                  <span>{percent}%</span>
                </div>
              </div>
              <div className="status-bar-track">
                <div className="status-bar-fill" style={{ width: `${percent}%` }} />
              </div>
            </div>
          ))}
        </div>

        {/* Recommended jobs section */}
        <section className="recommended-panel">
          <h3>Recommended Jobs</h3>
          <RecommendedJobs cards={allCards} page={recPage} onPage={(p) => setRecPage(p)} />
        </section>
      </section>

      <div className="board-section">
        <button type="button" className="board-nav left" onClick={() => scrollStages('left')}>&larr;</button>
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <div
            ref={stageScrollRef}
            className="board-scroller"
            onPointerEnter={() => setIsAutoScrollPaused(true)}
            onPointerLeave={() => setIsAutoScrollPaused(false)}
          >
            {COLUMN_ORDER.map((stage) => (
              <DropColumn
                key={stage}
                id={stage}
                title={STATUS_LABELS[stage]}
                count={statusTotals[stage] || 0}
                onAdd={openForm}
              >
                {filteredCards
                  .filter((card) => card.stage === stage)
                  .map((card) => (
                    <DraggableCard
                      key={card.id}
                      card={card}
                      searchQuery={searchQuery}
                      onSelect={() => {}}
                      onEdit={openEdit}
                      onDelete={handleDelete}
                      onUploadResume={handleUploadResume}
                      onRemoveResume={handleRemoveResume}
                    />
                  ))}
                { (columns[stage] || []).length === 0 && <div className="empty-column">No cards yet</div>}
              </DropColumn>
            ))}
          </div>
        </DndContext>
        <button type="button" className="board-nav right" onClick={() => scrollStages('right')}>&rarr;</button>
      </div>

      {modalOpen && (
        <div className="modal-backdrop" onClick={() => setModalOpen(false)}>
          <form className="modal-panel" onSubmit={handleSave} onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingCard ? 'Edit application' : 'Add new application'}</h2>
              <button type="button" className="close-button" onClick={() => setModalOpen(false)}>
                ×
              </button>
            </div>
            <div className="field-grid">
              <label>
                Job title <span className="required">*</span>
                <input
                  value={formState.role}
                  onChange={(event) => setFormState({ ...formState, role: event.target.value })}
                  required
                />
              </label>
              <label>
                Job description
                <textarea
                  rows="4"
                  value={formState.notes}
                  onChange={(event) => setFormState({ ...formState, notes: event.target.value })}
                />
              </label>
              <label>
                HR email
                <input
                  type="email"
                  value={formState.email}
                  onChange={(event) => setFormState({ ...formState, email: event.target.value })}
                />
              </label>
              <label>
                Phone number
                <input
                  type="tel"
                  value={formState.phone}
                  onChange={(event) => setFormState({ ...formState, phone: event.target.value })}
                />
              </label>
              <label>
                Upload Resume
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (!f) return;
                    const reader = new FileReader();
                    reader.onload = (ev) => {
                      setFormState({ ...formState, resume: { name: f.name, dataUrl: ev.target.result } });
                    };
                    reader.readAsDataURL(f);
                  }}
                />
                {formState.resume && formState.resume.name && (
                  <div className="muted resume-row">
                    📄 {formState.resume.name}
                    <button type="button" className="tiny" onClick={() => setFormState({ ...formState, resume: null })}>Remove</button>
                  </div>
                )}
              </label>
              <label>
                Choose card <span className="required">*</span>
                <select value={formState.stage} onChange={(event) => setFormState({ ...formState, stage: event.target.value })} required>
                  {COLUMN_ORDER.map((stageId) => (
                    <option key={stageId} value={stageId}>{STATUS_LABELS[stageId]}</option>
                  ))}
                </select>
              </label>
              <label>
                Company name
                <input
                  value={formState.company}
                  onChange={(event) => setFormState({ ...formState, company: event.target.value })}
                />
              </label>
              <label className="full-width required-note">
                Required fields: Job title and Choose card. The rest are optional.
              </label>
            </div>
            <div className="modal-footer">
              <button type="button" className="secondary" onClick={() => setModalOpen(false)}>
                Cancel
              </button>
              <button type="submit">Confirm</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

export default App;
