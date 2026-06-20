import React from 'react';

export default function TicketSourceToggle({ dataSource, onDataSourceChange, ticketId, onTicketIdChange, placeholder }) {
  return (
    <div className="genrow">
      <div className="source-pills">
        <button
          type="button"
          className={dataSource === 'jira' ? 'active' : ''}
          onClick={() => onDataSourceChange('jira')}
        >
          Jira
        </button>
        <button
          type="button"
          className={dataSource === 'azure' ? 'active' : ''}
          onClick={() => onDataSourceChange('azure')}
        >
          Azure DevOps
        </button>
      </div>
      <input
        className="jira-input"
        value={ticketId}
        onChange={(e) => onTicketIdChange(e.target.value)}
        placeholder={placeholder || (dataSource === 'azure' ? '1234' : 'VWO-48')}
        spellCheck="false"
      />
    </div>
  );
}
