import React from 'react';

function RecommendedJobs(props) {
  const cards = props.cards || [];
  const page = typeof props.page === 'number' ? props.page : 0;
  const onPage = typeof props.onPage === 'function' ? props.onPage : () => {};
  const pageSize = 5;

  const seen = new Set();
  const queries = [];

  cards.forEach((card) => {
    const query = ((card.role || '') + ' ' + (card.company || '')).trim();
    if (query && !seen.has(query)) {
      seen.add(query);
      queries.push(query);
    }
  });

  if (queries.length === 0) {
    return <div className="muted">Add job card to see job recommendations</div>;
  }

  const start = page * pageSize;
  const visible = queries.slice(start, start + pageSize);

  return (
    <div className="recommended-list">
      {visible.map((q, idx) => {
        const query = encodeURIComponent(q);
        return (
          <div key={start + idx} className="recommend-row">
            <div className="recommend-title">{q}</div>
            <div className="recommend-links">
              <a target="_blank" rel="noreferrer" href={`https://www.google.com/search?q=${query}+jobs`}>Google Jobs</a>
              <a target="_blank" rel="noreferrer" href={`https://www.linkedin.com/jobs/search/?keywords=${query}`}>LinkedIn</a>
              <a target="_blank" rel="noreferrer" href={`https://www.indeed.com/jobs?q=${query}`}>Indeed</a>
            </div>
          </div>
        );
      })}
      <div className="recommend-pagination">
        <button type="button" onClick={() => onPage(Math.max(0, page - 1))} disabled={page === 0}>Prev</button>
        <button type="button" onClick={() => onPage(page + 1)} disabled={(start + pageSize) >= queries.length}>Next</button>
      </div>
    </div>
  );
}

export default RecommendedJobs;
